import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const SHAPE_LIBRARY = {
  cube: {
    id: "cube",
    name: "Cubo 1x1x1",
    cells: [{ x: 0, y: 0, z: 0 }],
  },
  beamX: {
    id: "beamX",
    name: "Barra 2x1x1",
    cells: [
      { x: 0, y: 0, z: 0 },
      { x: 1, y: 0, z: 0 },
    ],
  },
  pillarY: {
    id: "pillarY",
    name: "Pilar 1x2x1",
    cells: [
      { x: 0, y: 0, z: 0 },
      { x: 0, y: 1, z: 0 },
    ],
  },
};

const occupiedCells = new Map();
const cursor = { x: 0, y: 0, z: 0 };
let activeShapeId = "cube";

const canvas = document.querySelector("#viewportCanvas");
const shapeSelect = document.querySelector("#shapeSelect");
const placeButton = document.querySelector("#placeButton");
const exportButton = document.querySelector("#exportButton");
const resetButton = document.querySelector("#resetButton");
const cursorReadout = document.querySelector("#cursorReadout");
const voxelReadout = document.querySelector("#voxelReadout");
const triangleReadout = document.querySelector("#triangleReadout");

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x08171e);
scene.fog = new THREE.Fog(0x08171e, 18, 54);

const camera = new THREE.PerspectiveCamera(48, 1, 0.1, 250);
camera.position.set(8.5, 9.5, 10.5);

const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  alpha: false,
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;

const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.target.set(2, 1, 2);
controls.minDistance = 4;
controls.maxDistance = 40;
controls.maxPolarAngle = Math.PI * 0.49;

const ambientLight = new THREE.HemisphereLight(0xb7f2ff, 0x102126, 1.25);
scene.add(ambientLight);

const mainLight = new THREE.DirectionalLight(0xfff0d0, 1.3);
mainLight.position.set(12, 18, 8);
scene.add(mainLight);

const rimLight = new THREE.DirectionalLight(0x56d0d7, 0.8);
rimLight.position.set(-10, 9, -12);
scene.add(rimLight);

const floor = new THREE.Mesh(
  new THREE.PlaneGeometry(120, 120),
  new THREE.MeshStandardMaterial({
    color: 0x0d2027,
    roughness: 0.96,
    metalness: 0.02,
  }),
);
floor.rotation.x = -Math.PI / 2;
floor.position.y = -0.001;
scene.add(floor);

const grid = new THREE.GridHelper(120, 120, 0x2d7c86, 0x163c45);
grid.position.y = 0;
scene.add(grid);

const modelMaterial = new THREE.MeshStandardMaterial({
  color: 0x6ee7d8,
  roughness: 0.38,
  metalness: 0.08,
});

const modelMesh = new THREE.Mesh(new THREE.BufferGeometry(), modelMaterial);
scene.add(modelMesh);

const edgeMaterial = new THREE.LineBasicMaterial({
  color: 0x021015,
  transparent: true,
  opacity: 0.55,
});
const modelEdges = new THREE.LineSegments(new THREE.BufferGeometry(), edgeMaterial);
scene.add(modelEdges);

const cursorGroup = new THREE.Group();
scene.add(cursorGroup);

const previewBoxGeometry = new THREE.BoxGeometry(0.94, 0.94, 0.94);
const previewEdgeGeometry = new THREE.EdgesGeometry(new THREE.BoxGeometry(1.02, 1.02, 1.02));
const previewFillMaterial = new THREE.MeshBasicMaterial({
  color: 0xffb347,
  transparent: true,
  opacity: 0.18,
  depthWrite: false,
});
const previewLineMaterial = new THREE.LineBasicMaterial({
  color: 0xffc86b,
  transparent: true,
  opacity: 0.9,
});

const verticalMovementMap = {
  KeyQ: { x: 0, y: 1, z: 0 },
  KeyE: { x: 0, y: -1, z: 0 },
  PageUp: { x: 0, y: 1, z: 0 },
  PageDown: { x: 0, y: -1, z: 0 },
};
const cameraForward = new THREE.Vector3();
const lastHorizontalForward = new THREE.Vector3(0, 0, -1);

function buildShapeSelector() {
  Object.values(SHAPE_LIBRARY).forEach((shape) => {
    const option = document.createElement("option");
    option.value = shape.id;
    option.textContent = shape.name;
    shapeSelect.append(option);
  });
  shapeSelect.value = activeShapeId;
}

function cellKey(x, y, z) {
  return `${x},${y},${z}`;
}

function shapeWorldCells(shapeId, anchor) {
  return SHAPE_LIBRARY[shapeId].cells.map((cell) => ({
    x: anchor.x + cell.x,
    y: anchor.y + cell.y,
    z: anchor.z + cell.z,
  }));
}

function getCameraRelativeDelta(keyCode) {
  camera.getWorldDirection(cameraForward);
  cameraForward.y = 0;

  if (cameraForward.lengthSq() < 1e-6) {
    cameraForward.copy(lastHorizontalForward);
  } else if (Math.abs(cameraForward.x) >= Math.abs(cameraForward.z)) {
    cameraForward.set(Math.sign(cameraForward.x) || 1, 0, 0);
    lastHorizontalForward.copy(cameraForward);
  } else {
    cameraForward.set(0, 0, Math.sign(cameraForward.z) || 1);
    lastHorizontalForward.copy(cameraForward);
  }

  const forward = { x: cameraForward.x, y: 0, z: cameraForward.z };
  const right = { x: -forward.z, y: 0, z: forward.x };

  switch (keyCode) {
    case "ArrowUp":
      return forward;
    case "ArrowDown":
      return { x: -forward.x, y: 0, z: -forward.z };
    case "ArrowLeft":
      return { x: -right.x, y: 0, z: -right.z };
    case "ArrowRight":
      return right;
    default:
      return null;
  }
}

function clearCursorPreview() {
  while (cursorGroup.children.length > 0) {
    cursorGroup.remove(cursorGroup.children[0]);
  }
}

function updateCursorPreview() {
  clearCursorPreview();

  const ghostCells = shapeWorldCells(activeShapeId, cursor);
  ghostCells.forEach((cell) => {
    const previewMesh = new THREE.Mesh(previewBoxGeometry, previewFillMaterial);
    previewMesh.position.set(cell.x + 0.5, cell.y + 0.5, cell.z + 0.5);

    const previewEdges = new THREE.LineSegments(
      previewEdgeGeometry,
      previewLineMaterial,
    );
    previewEdges.position.copy(previewMesh.position);

    cursorGroup.add(previewMesh, previewEdges);
  });
}

function updateReadout() {
  const geometry = modelMesh.geometry;
  const index = geometry.getIndex();
  const triangleCount = index ? index.count / 3 : 0;

  cursorReadout.textContent = `${cursor.x}, ${cursor.y}, ${cursor.z}`;
  voxelReadout.textContent = `${occupiedCells.size}`;
  triangleReadout.textContent = `${triangleCount}`;
}

function addShape(anchor, shapeId) {
  let changed = false;

  shapeWorldCells(shapeId, anchor).forEach((cell) => {
    const key = cellKey(cell.x, cell.y, cell.z);
    if (!occupiedCells.has(key)) {
      occupiedCells.set(key, cell);
      changed = true;
    }
  });

  if (changed) {
    rebuildMergedMesh();
  } else {
    updateReadout();
  }
}

function makePoint(axis, uAxis, vAxis, plane, u, v) {
  const point = [0, 0, 0];
  point[axis] = plane;
  point[uAxis] = u;
  point[vAxis] = v;
  return point;
}

function cross(a, b) {
  return [
    a[1] * b[2] - a[2] * b[1],
    a[2] * b[0] - a[0] * b[2],
    a[0] * b[1] - a[1] * b[0],
  ];
}

function subtract(a, b) {
  return [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
}

function dot(a, b) {
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}

function emitQuad({
  axis,
  direction,
  plane,
  uAxis,
  vAxis,
  u,
  v,
  width,
  height,
  addVertex,
  indices,
}) {
  const desiredNormal = [0, 0, 0];
  desiredNormal[axis] = direction;

  const p0 = makePoint(axis, uAxis, vAxis, plane, u, v);
  const p1 = makePoint(axis, uAxis, vAxis, plane, u + width, v);
  const p2 = makePoint(axis, uAxis, vAxis, plane, u + width, v + height);
  const p3 = makePoint(axis, uAxis, vAxis, plane, u, v + height);

  const computedNormal = cross(subtract(p1, p0), subtract(p2, p0));
  const corners =
    dot(computedNormal, desiredNormal) >= 0 ? [p0, p1, p2, p3] : [p0, p3, p2, p1];

  const i0 = addVertex(corners[0], desiredNormal);
  const i1 = addVertex(corners[1], desiredNormal);
  const i2 = addVertex(corners[2], desiredNormal);
  const i3 = addVertex(corners[3], desiredNormal);

  indices.push(i0, i1, i2, i0, i2, i3);
}

function buildMergedGeometry() {
  const geometry = new THREE.BufferGeometry();

  if (occupiedCells.size === 0) {
    return geometry;
  }

  const cells = Array.from(occupiedCells.values());
  const bounds = {
    min: [Infinity, Infinity, Infinity],
    max: [-Infinity, -Infinity, -Infinity],
  };

  cells.forEach((cell) => {
    bounds.min[0] = Math.min(bounds.min[0], cell.x);
    bounds.min[1] = Math.min(bounds.min[1], cell.y);
    bounds.min[2] = Math.min(bounds.min[2], cell.z);
    bounds.max[0] = Math.max(bounds.max[0], cell.x);
    bounds.max[1] = Math.max(bounds.max[1], cell.y);
    bounds.max[2] = Math.max(bounds.max[2], cell.z);
  });

  const positions = [];
  const normals = [];
  const indices = [];
  const vertexMap = new Map();

  const addVertex = (point, normal) => {
    const key = `${point[0]},${point[1]},${point[2]}|${normal[0]},${normal[1]},${normal[2]}`;
    if (vertexMap.has(key)) {
      return vertexMap.get(key);
    }

    const index = positions.length / 3;
    positions.push(point[0], point[1], point[2]);
    normals.push(normal[0], normal[1], normal[2]);
    vertexMap.set(key, index);
    return index;
  };

  for (let axis = 0; axis < 3; axis += 1) {
    const remainingAxes = [0, 1, 2].filter((candidate) => candidate !== axis);
    const [uAxis, vAxis] = remainingAxes;
    const uMin = bounds.min[uAxis];
    const vMin = bounds.min[vAxis];
    const uSize = bounds.max[uAxis] - bounds.min[uAxis] + 1;
    const vSize = bounds.max[vAxis] - bounds.min[vAxis] + 1;

    [-1, 1].forEach((direction) => {
      const slices = new Map();

      cells.forEach((cell) => {
        const coord = [cell.x, cell.y, cell.z];
        const neighbor = [...coord];
        neighbor[axis] += direction;

        if (occupiedCells.has(cellKey(neighbor[0], neighbor[1], neighbor[2]))) {
          return;
        }

        const plane = coord[axis] + (direction > 0 ? 1 : 0);
        const sliceKey = `${coord[uAxis]},${coord[vAxis]}`;

        if (!slices.has(plane)) {
          slices.set(plane, new Set());
        }
        slices.get(plane).add(sliceKey);
      });

      slices.forEach((faceSet, plane) => {
        const mask = new Array(uSize * vSize).fill(false);

        faceSet.forEach((entry) => {
          const [u, v] = entry.split(",").map(Number);
          const index = (v - vMin) * uSize + (u - uMin);
          mask[index] = true;
        });

        for (let v = 0; v < vSize; v += 1) {
          for (let u = 0; u < uSize; ) {
            const index = v * uSize + u;

            if (!mask[index]) {
              u += 1;
              continue;
            }

            let width = 1;
            while (u + width < uSize && mask[index + width]) {
              width += 1;
            }

            let height = 1;
            let keepGrowing = true;

            while (v + height < vSize && keepGrowing) {
              for (let offset = 0; offset < width; offset += 1) {
                if (!mask[(v + height) * uSize + u + offset]) {
                  keepGrowing = false;
                  break;
                }
              }

              if (keepGrowing) {
                height += 1;
              }
            }

            for (let row = 0; row < height; row += 1) {
              for (let column = 0; column < width; column += 1) {
                mask[(v + row) * uSize + u + column] = false;
              }
            }

            emitQuad({
              axis,
              direction,
              plane,
              uAxis,
              vAxis,
              u: uMin + u,
              v: vMin + v,
              width,
              height,
              addVertex,
              indices,
            });

            u += width;
          }
        }
      });
    });
  }

  geometry.setAttribute(
    "position",
    new THREE.Float32BufferAttribute(positions, 3),
  );
  geometry.setAttribute("normal", new THREE.Float32BufferAttribute(normals, 3));
  geometry.setIndex(indices);
  geometry.computeBoundingSphere();
  return geometry;
}

function rebuildMergedMesh() {
  const nextGeometry = buildMergedGeometry();

  modelMesh.geometry.dispose();
  modelMesh.geometry = nextGeometry;

  const nextEdges = nextGeometry.index
    ? new THREE.EdgesGeometry(nextGeometry, 1)
    : new THREE.BufferGeometry();

  modelEdges.geometry.dispose();
  modelEdges.geometry = nextEdges;

  updateReadout();
}

function moveCursorAndPlace(delta) {
  cursor.x += delta.x;
  cursor.y = Math.max(0, cursor.y + delta.y);
  cursor.z += delta.z;
  addShape(cursor, activeShapeId);
  updateCursorPreview();
}

function exportOBJ() {
  const geometry = modelMesh.geometry;
  const position = geometry.getAttribute("position");
  const normal = geometry.getAttribute("normal");
  const index = geometry.getIndex();

  if (!position || !normal || !index || index.count === 0) {
    window.alert("No hay geometría para exportar.");
    return;
  }

  const lines = [
    "# EMS 3D Model Editor",
    "# Exportacion OBJ fusionada",
    "o ModeloFusionado",
  ];

  for (let i = 0; i < position.count; i += 1) {
    lines.push(
      `v ${position.getX(i).toFixed(6)} ${position.getY(i).toFixed(6)} ${position.getZ(i).toFixed(6)}`,
    );
  }

  for (let i = 0; i < normal.count; i += 1) {
    lines.push(
      `vn ${normal.getX(i).toFixed(6)} ${normal.getY(i).toFixed(6)} ${normal.getZ(i).toFixed(6)}`,
    );
  }

  for (let i = 0; i < index.count; i += 3) {
    const a = index.getX(i) + 1;
    const b = index.getX(i + 1) + 1;
    const c = index.getX(i + 2) + 1;
    lines.push(`f ${a}//${a} ${b}//${b} ${c}//${c}`);
  }

  const blob = new Blob([`${lines.join("\n")}\n`], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "modelo-fusionado.obj";
  link.click();
  URL.revokeObjectURL(url);
}

function resetModel() {
  occupiedCells.clear();
  cursor.x = 0;
  cursor.y = 0;
  cursor.z = 0;
  addShape(cursor, "cube");
  updateCursorPreview();
}

function handleKeyDown(event) {
  const activeTag = document.activeElement?.tagName;
  if (activeTag === "INPUT" || activeTag === "TEXTAREA" || activeTag === "SELECT") {
    return;
  }

  const movementDelta = verticalMovementMap[event.code] ?? getCameraRelativeDelta(event.code);

  if (movementDelta) {
    event.preventDefault();
    moveCursorAndPlace(movementDelta);
    return;
  }

  if (event.code === "Space" || event.code === "Enter") {
    event.preventDefault();
    addShape(cursor, activeShapeId);
    updateCursorPreview();
  }
}

function resizeRenderer() {
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;

  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

function animate() {
  controls.update();
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}

function wireEvents() {
  shapeSelect.addEventListener("change", () => {
    activeShapeId = shapeSelect.value;
    updateCursorPreview();
  });

  placeButton.addEventListener("click", () => {
    addShape(cursor, activeShapeId);
    updateCursorPreview();
  });

  exportButton.addEventListener("click", exportOBJ);
  resetButton.addEventListener("click", resetModel);
  window.addEventListener("keydown", handleKeyDown);
  window.addEventListener("resize", resizeRenderer);
}

function init() {
  buildShapeSelector();
  wireEvents();
  resizeRenderer();
  resetModel();
  animate();
}

init();
