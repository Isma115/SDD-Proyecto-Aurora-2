import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  runApp(const AuroraApp());
}

class AuroraApp extends StatelessWidget {
  const AuroraApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Aurora',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF075E54),
          primary: const Color(0xFF075E54),
          secondary: const Color(0xFF128C7E),
        ),
        scaffoldBackgroundColor: const Color(0xFFECE5DD),
        useMaterial3: true,
      ),
      home: const MainScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Modelos
// ─────────────────────────────────────────────────────────────────────────────

class ChatMessage {
  final String text;
  final bool isUser;

  ChatMessage({required this.text, required this.isUser});
}

// ─────────────────────────────────────────────────────────────────────────────
// Pantalla principal con BottomNavigationBar
// ─────────────────────────────────────────────────────────────────────────────

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _currentIndex = 0;
  String _serverIp = '192.168.1.100:8000';

  @override
  void initState() {
    super.initState();
    _loadServerIp();
  }

  Future<void> _loadServerIp() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _serverIp = prefs.getString('server_ip') ?? '192.168.1.100:8000';
    });
  }

  void _updateServerIp(String ip) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('server_ip', ip);
    setState(() {
      _serverIp = ip;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: [
          ChatScreen(
            serverIp: _serverIp,
            onSettingsChanged: _updateServerIp,
          ),
          StatsScreen(serverIp: _serverIp),
        ],
      ),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          boxShadow: [
            BoxShadow(color: Colors.black12, blurRadius: 8, offset: Offset(0, -2)),
          ],
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: (i) => setState(() => _currentIndex = i),
          backgroundColor: const Color(0xFF075E54),
          selectedItemColor: const Color(0xFF25D366),
          unselectedItemColor: Colors.white70,
          type: BottomNavigationBarType.fixed,
          selectedLabelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
          unselectedLabelStyle: const TextStyle(fontSize: 12),
          items: const [
            BottomNavigationBarItem(icon: Icon(Icons.chat_bubble), label: 'Chat'),
            BottomNavigationBarItem(icon: Icon(Icons.bar_chart_rounded), label: 'Estadísticas'),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Pantalla de Chat (refactorizada sin Scaffold propio)
// ─────────────────────────────────────────────────────────────────────────────

class ChatScreen extends StatefulWidget {
  final String serverIp;
  final Function(String) onSettingsChanged;

  const ChatScreen({super.key, required this.serverIp, required this.onSettingsChanged});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final List<ChatMessage> _messages = [];
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  bool _isLoading = false;
  String _currentIp = '';

  @override
  void initState() {
    super.initState();
    _currentIp = widget.serverIp;
    _loadHistory();
  }

  @override
  void didUpdateWidget(ChatScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.serverIp != oldWidget.serverIp) {
      _currentIp = widget.serverIp;
      _loadHistory();
    }
  }

  Future<void> _loadHistory() async {
    try {
      final response = await http
          .get(Uri.parse('http://$_currentIp/history'))
          .timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final List prevMessages = data['mensajes'];
        setState(() {
          _messages.clear();
          for (var msg in prevMessages) {
            _messages.add(ChatMessage(
              text: msg['content'],
              isUser: msg['role'] == 'user',
            ));
          }
        });
        _scrollToBottom();
      }
    } catch (e) {
      debugPrint("No se pudo cargar el historial: $e");
    }
  }

  void _showSettingsDialog() {
    final TextEditingController ipController = TextEditingController(text: _currentIp);
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Configuración Servidor'),
          content: TextField(
            controller: ipController,
            decoration: const InputDecoration(
              labelText: 'IP:Puerto (ej: 192.168.1.55:8000)',
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancelar'),
            ),
            ElevatedButton(
              onPressed: () {
                widget.onSettingsChanged(ipController.text);
                Navigator.pop(context);
              },
              child: const Text('Guardar'),
            ),
          ],
        );
      },
    );
  }

  Future<void> _sendMessage(String text) async {
    if (text.trim().isEmpty) return;

    final userMsg = ChatMessage(text: text, isUser: true);
    setState(() {
      _messages.add(userMsg);
      _isLoading = true;
    });
    _textController.clear();
    _scrollToBottom();

    try {
      final response = await http
          .post(
            Uri.parse('http://$_currentIp/chat'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'mensaje': text}),
          )
          .timeout(const Duration(seconds: 60));

      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));
        setState(() {
          _messages.add(ChatMessage(text: data['respuesta'], isUser: false));
        });
      } else {
        setState(() {
          _messages.add(ChatMessage(text: '[Error: ${response.statusCode}]', isUser: false));
        });
      }
    } catch (e) {
      setState(() {
        _messages.add(ChatMessage(
            text: '[Error de conexión: Verifica la IP del servidor]', isUser: false));
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
      _scrollToBottom();
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            CircleAvatar(
              backgroundColor: Colors.white,
              child: Icon(Icons.person, color: Color(0xFF075E54)),
            ),
            SizedBox(width: 10),
            Text('Aurora', style: TextStyle(color: Colors.white)),
          ],
        ),
        backgroundColor: const Color(0xFF075E54),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings, color: Colors.white),
            onPressed: _showSettingsDialog,
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(10),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[index];
                return MessageBubble(message: message);
              },
            ),
          ),
          if (_isLoading)
            const Padding(
              padding: EdgeInsets.all(8.0),
              child: Row(
                children: [
                  SizedBox(width: 16),
                  SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                  SizedBox(width: 8),
                  Text("Aurora está escribiendo...",
                      style: TextStyle(color: Colors.grey)),
                ],
              ),
            ),
          _buildMessageInput(),
        ],
      ),
    );
  }

  Widget _buildMessageInput() {
    return Container(
      color: Colors.transparent,
      padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 8.0),
      child: Row(
        children: [
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(24.0),
                boxShadow: [
                  BoxShadow(
                    offset: const Offset(0, 2),
                    blurRadius: 2,
                    color: Colors.black.withOpacity(0.1),
                  )
                ],
              ),
              child: Row(
                children: [
                  const SizedBox(width: 16),
                  Expanded(
                    child: TextField(
                      controller: _textController,
                      decoration: const InputDecoration(
                        hintText: "Mensaje",
                        border: InputBorder.none,
                      ),
                      textCapitalization: TextCapitalization.sentences,
                      maxLines: null,
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.mic, color: Colors.grey),
                    onPressed: () {},
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(width: 8),
          Container(
            decoration: const BoxDecoration(
              color: Color(0xFF128C7E),
              shape: BoxShape.circle,
            ),
            child: IconButton(
              icon: const Icon(Icons.send, color: Colors.white),
              onPressed: () {
                _sendMessage(_textController.text);
              },
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Burbuja de mensaje
// ─────────────────────────────────────────────────────────────────────────────

class MessageBubble extends StatelessWidget {
  final ChatMessage message;

  const MessageBubble({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: message.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 14),
        decoration: BoxDecoration(
          color: message.isUser ? const Color(0xFFDCF8C6) : Colors.white,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              offset: const Offset(0, 1),
              blurRadius: 1,
              color: Colors.black.withOpacity(0.1),
            )
          ],
        ),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.75,
        ),
        child: Text(
          message.text,
          style: const TextStyle(fontSize: 16, color: Colors.black87),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Pantalla de Estadísticas
// ─────────────────────────────────────────────────────────────────────────────

class StatsScreen extends StatefulWidget {
  final String serverIp;

  const StatsScreen({super.key, required this.serverIp});

  @override
  State<StatsScreen> createState() => _StatsScreenState();
}

class _StatsScreenState extends State<StatsScreen> with SingleTickerProviderStateMixin {
  Map<String, dynamic>? _stats;
  bool _loading = true;
  String? _error;
  Timer? _refreshTimer;
  late AnimationController _animController;
  late Animation<double> _fadeAnim;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _fadeAnim = CurvedAnimation(parent: _animController, curve: Curves.easeOut);
    _loadStats();
    _refreshTimer = Timer.periodic(const Duration(seconds: 10), (_) => _loadStats());
  }

  @override
  void didUpdateWidget(StatsScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.serverIp != oldWidget.serverIp) {
      _loadStats();
    }
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    _animController.dispose();
    super.dispose();
  }

  Future<void> _loadStats() async {
    try {
      final response = await http
          .get(Uri.parse('http://${widget.serverIp}/stats'))
          .timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));
        setState(() {
          _stats = data;
          _loading = false;
          _error = null;
        });
        _animController.forward(from: 0);
      } else {
        setState(() {
          _loading = false;
          _error = 'Error ${response.statusCode}';
        });
      }
    } catch (e) {
      setState(() {
        _loading = false;
        _error = 'No se pudo conectar al servidor';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            Icon(Icons.bar_chart_rounded, color: Colors.white),
            SizedBox(width: 10),
            Text('Estadísticas', style: TextStyle(color: Colors.white)),
          ],
        ),
        backgroundColor: const Color(0xFF075E54),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.white),
            onPressed: () {
              setState(() => _loading = true);
              _loadStats();
            },
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_loading && _stats == null) {
      return const Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircularProgressIndicator(color: Color(0xFF128C7E)),
            SizedBox(height: 16),
            Text('Cargando estadísticas...', style: TextStyle(color: Colors.grey)),
          ],
        ),
      );
    }

    if (_error != null && _stats == null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.cloud_off, size: 64, color: Colors.grey),
            const SizedBox(height: 16),
            Text(_error!, style: const TextStyle(color: Colors.grey, fontSize: 16)),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: _loadStats,
              icon: const Icon(Icons.refresh),
              label: const Text('Reintentar'),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF128C7E),
                foregroundColor: Colors.white,
              ),
            ),
          ],
        ),
      );
    }

    return FadeTransition(
      opacity: _fadeAnim,
      child: RefreshIndicator(
        onRefresh: _loadStats,
        color: const Color(0xFF25D366),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _buildHeader(),
            const SizedBox(height: 16),
            _buildStatCardsRow(),
            const SizedBox(height: 16),
            _buildRoundIndicator(),
            const SizedBox(height: 16),
            _buildLevelBar(),
            const SizedBox(height: 16),
            _buildProgressChart(),
            const SizedBox(height: 16),
            _buildExtraStats(),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '📊  Estadísticas de Progreso',
          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Color(0xFF111B21)),
        ),
        const SizedBox(height: 4),
        Text(
          'Sigue tu mejora conversacional con Aurora',
          style: TextStyle(fontSize: 13, color: Colors.grey[600]),
        ),
      ],
    );
  }

  Widget _buildStatCardsRow() {
    final s = _stats!;
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 12,
      crossAxisSpacing: 12,
      childAspectRatio: 1.6,
      children: [
        _StatCard(emoji: '📨', title: 'Mensajes totales', value: '${s["mensajes_totales"] ?? 0}', accentColor: const Color(0xFF25D366)),
        _StatCard(emoji: '🏆', title: 'Récord 5 min', value: '${s["record_5min"] ?? 0}', accentColor: const Color(0xFF53BDEB)),
        _StatCard(emoji: '🔥', title: 'Racha de días', value: '${s["racha_dias"] ?? 0}', accentColor: const Color(0xFFFF6B6B)),
        _StatCard(emoji: '💬', title: 'Conversaciones', value: '${s["total_conversaciones"] ?? 0}', accentColor: const Color(0xFF25D366)),
      ],
    );
  }

  Widget _buildRoundIndicator() {
    final ronda = _stats?["ronda_actual"] ?? {};
    final activa = ronda["activa"] == true;
    final msgs = ronda["mensajes"] ?? 0;
    final segsRestantes = ronda["segundos_restantes"] ?? 0;
    final mins = segsRestantes ~/ 60;
    final secs = segsRestantes % 60;
    final progreso = activa ? segsRestantes / 300.0 : 0.0;

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('⏱  Ronda de 5 minutos',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: activa ? const Color(0xFF25D366).withOpacity(0.15) : Colors.grey.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    activa ? '🟢 Activo' : 'Inactivo',
                    style: TextStyle(
                      color: activa ? const Color(0xFF25D366) : Colors.grey,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Mensajes: $msgs', style: const TextStyle(fontSize: 14)),
                Text(
                  activa ? 'Tiempo: ${mins.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}' : 'Tiempo: --:--',
                  style: const TextStyle(fontSize: 14),
                ),
              ],
            ),
            const SizedBox(height: 8),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: progreso.toDouble(),
                minHeight: 6,
                backgroundColor: Colors.grey[200],
                valueColor: const AlwaysStoppedAnimation(Color(0xFF25D366)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLevelBar() {
    final nivel = _stats?["nivel"] ?? {};
    final nombre = nivel["nombre"] ?? "Principiante";
    final emoji = nivel["emoji"] ?? "🌱";
    final progreso = (nivel["progreso"] ?? 0.0).toDouble();
    final totalMsgs = nivel["mensajes_totales"] ?? 0;
    final maxNivel = nivel["max_nivel"];

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('$emoji  $nombre',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                Text(
                  maxNivel != null ? '$totalMsgs / $maxNivel msgs' : '$totalMsgs msgs',
                  style: TextStyle(color: Colors.grey[600], fontSize: 12),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              maxNivel != null
                  ? 'Te faltan ${maxNivel - totalMsgs} mensajes para el siguiente nivel'
                  : '¡Has alcanzado el nivel máximo! 🎉',
              style: TextStyle(color: Colors.grey[500], fontSize: 12),
            ),
            const SizedBox(height: 10),
            Stack(
              children: [
                Container(
                  height: 20,
                  decoration: BoxDecoration(
                    color: Colors.grey[200],
                    borderRadius: BorderRadius.circular(10),
                  ),
                ),
                FractionallySizedBox(
                  widthFactor: progreso.clamp(0.0, 1.0),
                  child: Container(
                    height: 20,
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFF128C7E), Color(0xFF25D366)],
                      ),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    alignment: Alignment.center,
                    child: Text(
                      '${(progreso * 100).toInt()}%',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProgressChart() {
    final puntajes = (_stats?["puntajes_5min"] as List?)
            ?.map((p) => (p["puntaje"] as num?)?.toDouble() ?? 0.0)
            .toList() ??
        [];
    final record = (_stats?["record_5min"] as num?)?.toDouble() ?? 0.0;

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('📈  Progreso de Puntajes',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
            const SizedBox(height: 4),
            Text('Rondas de 5 minutos', style: TextStyle(color: Colors.grey[500], fontSize: 12)),
            const SizedBox(height: 16),
            SizedBox(
              height: 200,
              child: puntajes.isEmpty
                  ? Center(
                      child: Text('Aún no hay datos de rondas',
                          style: TextStyle(color: Colors.grey[400])))
                  : CustomPaint(
                      size: const Size(double.infinity, 200),
                      painter: _ChartPainter(
                        valores: puntajes.length > 20 ? puntajes.sublist(puntajes.length - 20) : puntajes,
                        record: record,
                        accentColor: const Color(0xFF25D366),
                        recordColor: const Color(0xFFFF6B6B),
                        gridColor: Colors.grey[200]!,
                        textColor: Colors.grey[500]!,
                      ),
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildExtraStats() {
    final s = _stats!;
    return Row(
      children: [
        Expanded(
          child: _StatCard(
            emoji: '📝',
            title: 'Mensaje más largo',
            value: '${s["mensaje_mas_largo"] ?? 0} chars',
            accentColor: const Color(0xFF53BDEB),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _StatCard(
            emoji: '📈',
            title: 'Promedio msg/conv',
            value: '${s["promedio_mensajes_conversacion"] ?? 0.0}',
            accentColor: const Color(0xFF25D366),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _StatCard(
            emoji: '📅',
            title: 'Días activos',
            value: '${s["dias_activos_total"] ?? 0}',
            accentColor: const Color(0xFF128C7E),
          ),
        ),
      ],
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Widgets reutilizables
// ─────────────────────────────────────────────────────────────────────────────

class _StatCard extends StatelessWidget {
  final String emoji;
  final String title;
  final String value;
  final Color accentColor;

  const _StatCard({
    required this.emoji,
    required this.title,
    required this.value,
    required this.accentColor,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              height: 3,
              decoration: BoxDecoration(
                color: accentColor,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(height: 8),
            Text(emoji, style: const TextStyle(fontSize: 22)),
            const SizedBox(height: 4),
            FittedBox(
              fit: BoxFit.scaleDown,
              alignment: Alignment.centerLeft,
              child: Text(
                value,
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: accentColor,
                ),
              ),
            ),
            const SizedBox(height: 2),
            Text(
              title,
              style: TextStyle(fontSize: 11, color: Colors.grey[600]),
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Canvas Painter para la gráfica de progreso
// ─────────────────────────────────────────────────────────────────────────────

class _ChartPainter extends CustomPainter {
  final List<double> valores;
  final double record;
  final Color accentColor;
  final Color recordColor;
  final Color gridColor;
  final Color textColor;

  _ChartPainter({
    required this.valores,
    required this.record,
    required this.accentColor,
    required this.recordColor,
    required this.gridColor,
    required this.textColor,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (valores.isEmpty) return;

    const mLeft = 35.0;
    const mRight = 15.0;
    const mTop = 15.0;
    const mBottom = 25.0;

    final areaW = size.width - mLeft - mRight;
    final areaH = size.height - mTop - mBottom;

    final maxVal = [valores.reduce((a, b) => a > b ? a : b), record, 1.0].reduce((a, b) => a > b ? a : b);

    // Grid
    final gridPaint = Paint()
      ..color = gridColor
      ..strokeWidth = 0.5;

    final textStyle = TextStyle(color: textColor, fontSize: 9);

    for (int i = 0; i <= 4; i++) {
      final y = mTop + (areaH * i / 4);
      canvas.drawLine(Offset(mLeft, y), Offset(size.width - mRight, y), gridPaint);

      final val = (maxVal * (1 - i / 4)).toInt();
      final tp = TextPainter(
        text: TextSpan(text: '$val', style: textStyle),
        textDirection: TextDirection.ltr,
      )..layout();
      tp.paint(canvas, Offset(mLeft - tp.width - 4, y - tp.height / 2));
    }

    // Record line
    if (record > 0) {
      final ry = mTop + areaH * (1 - record / maxVal);
      final recPaint = Paint()
        ..color = recordColor
        ..strokeWidth = 1.5
        ..style = PaintingStyle.stroke;

      const dashLen = 6.0;
      const gapLen = 3.0;
      var x = mLeft;
      while (x < size.width - mRight) {
        canvas.drawLine(Offset(x, ry), Offset((x + dashLen).clamp(0, size.width - mRight), ry), recPaint);
        x += dashLen + gapLen;
      }

      final tp = TextPainter(
        text: TextSpan(
          text: 'Récord: ${record.toInt()}',
          style: TextStyle(color: recordColor, fontSize: 9, fontWeight: FontWeight.bold),
        ),
        textDirection: TextDirection.ltr,
      )..layout();
      tp.paint(canvas, Offset(size.width - mRight - tp.width, ry - tp.height - 4));
    }

    final n = valores.length;
    final spacing = n > 1 ? areaW / (n - 1) : areaW / 2;

    final points = <Offset>[];
    for (int i = 0; i < n; i++) {
      final x = mLeft + (n > 1 ? i * spacing : areaW / 2);
      final y = mTop + areaH * (1 - valores[i] / maxVal);
      points.add(Offset(x, y));
    }

    // Fill area
    if (points.length >= 2) {
      final fillPath = Path()..moveTo(points.first.dx, points.first.dy);
      for (int i = 1; i < points.length; i++) {
        fillPath.lineTo(points[i].dx, points[i].dy);
      }
      fillPath.lineTo(points.last.dx, mTop + areaH);
      fillPath.lineTo(points.first.dx, mTop + areaH);
      fillPath.close();

      final fillPaint = Paint()
        ..color = accentColor.withOpacity(0.15)
        ..style = PaintingStyle.fill;
      canvas.drawPath(fillPath, fillPaint);
    }

    // Line
    if (points.length >= 2) {
      final linePaint = Paint()
        ..color = accentColor
        ..strokeWidth = 2.5
        ..style = PaintingStyle.stroke
        ..strokeCap = StrokeCap.round
        ..strokeJoin = StrokeJoin.round;

      final linePath = Path()..moveTo(points.first.dx, points.first.dy);
      for (int i = 1; i < points.length; i++) {
        linePath.lineTo(points[i].dx, points[i].dy);
      }
      canvas.drawPath(linePath, linePaint);
    }

    // Dots
    for (int i = 0; i < points.length; i++) {
      final isRec = valores[i] == record && record > 0;
      final dotColor = isRec ? recordColor : accentColor;

      canvas.drawCircle(points[i], 5, Paint()..color = Colors.white);
      canvas.drawCircle(points[i], 4, Paint()..color = dotColor);
    }

    // X axis labels
    for (int i = 0; i < points.length; i++) {
      if (n <= 10 || i % (n ~/ 10).clamp(1, n) == 0 || i == n - 1) {
        final tp = TextPainter(
          text: TextSpan(text: '${i + 1}', style: textStyle),
          textDirection: TextDirection.ltr,
        )..layout();
        tp.paint(canvas, Offset(points[i].dx - tp.width / 2, mTop + areaH + 6));
      }
    }
  }

  @override
  bool shouldRepaint(covariant _ChartPainter oldDelegate) {
    return oldDelegate.valores != valores || oldDelegate.record != record;
  }
}
