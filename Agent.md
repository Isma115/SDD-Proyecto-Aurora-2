La estructura base de código para una funcionalidad grande es la siguiente:

FrontEnd: Separación por vista funcionalidad, se debe separar las vistas de la funcionalidad, crear una carpeta vistas y otra carpeta de lógica para cada página, por ejemplo la carpeta frontend/src/pages/, podría tener dentro cada una de las páginas de la web, aplicación o software que desarrollemos, sería por ejemplo: frontend/src/pages/HomePage, y dentro de esa carpeta tendríamos dos más la de View y la de Logic, (o cualquier nombre más conveniente). La cuestión es que hay que separar cada funcionalidad y página de la web por ficheros de poco tamaño para mejorar la legibilidad sin caer en la sobremodularización
Backend: Separación por carpetas controllers/HomePage, por ejemplo, tendríamos los controladores para la HomePage, o models/cliente.js ahí ya no sería necesario clasificar modelos por carpetas
Componentes y útiles reutilizables, en una carpeta a parte dentro también de la parte de frontend (o backend en caso de que sean funcionalidades de base de datos reutilizables). Pero que sean globales estando apartada de las páginas

Como añadido, crea o edita un fichero markdown llamado: secciones.md, dónde vas a escribir según la página o sección del software que estés creando o editando, las partes del código que están utilizando, por ejemplo para una página Gestor de Clientes, secciones.md tendría:

Sección: Gestor de clientes:
frontend/src/pages/GestorClientes/Views/layout.JSX
frontend/src/pages/GestorClientes/Logic/layout.js
frontend/src/pages/GestorClientes/Views/PopUpCrearCliente.JSX
frontend/src/pages/GestorClientes/Logic/popupcrearcliente.js
frontend/src/styles/GestorClientes/gestorClientes.css
frontend/src/styles/general/botones.css
backend/src/models/cliente.model.js
backend/src/controllers/gestorclientes.controller.js

Entonces para cada parte de la aplicación por ejemplo para una hipotética página de gestión de clientes, tendríamos en ese MD, dicha parte de la aplicación y a continuación tendríamos el listado de todos los ficheros de código involucrados en esa parte de la aplicación, sin añadir


Para cada funcionalidad específica de la aplicación tiene que existir lo que se llama "segmento de código" lo cual es la compilación de las estructuras de código que involucran una funcionalidad específica. En el documento markdown de secciones.md, a parte, para cada funcionalidad específica se tiene que incluir el listado de todas las estructuras de código que involucran una funcionalidad específica, funciones, clases, etiquetas, componentes, estructuras, etc. listando sus cabeceras para cada funcionalidad, por ejemplo:

Sección: Calculadora
ficheros calculadora:
frontend/src/components/Calculadora/Suma.jsx
frontend/src/components/Calculadora/Resta.jsx
frontend/src/components/Calculadora/Layout.jsx

Segmento: Operaciones de suma y resta
function sumar(a, b){
function restar(a, b){
return (<(componente jsx)>)
class Calculadora { 

Segmento: Vista Suma y resta
function Suma(a, b){
return (<(componente jsx)>)


El listado de cada segmento de código como el anterior debe estar definido dentro de la propia sección definida para cada parte o funcionalidad de la aplicación en el archivo secciones.md a continuación de la definición de la lista de ficheros de dicha sección, para cada sección definida pueden haber varios segmentos de código. Cada segmento debe tener solamente la funcionalidad imprescindible, se atomiza cada funcionalidad completa en tantos segmentos de código como sea necesario, por ejemplo para una funcionalidad de calculadora tendremos los segmentos: vista suma y resta, vista resta, vista layout, operaciones de suma y resta, operaciones de resta, layout calculadora, etc.