import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import * as THREE from "three";

gsap.registerPlugin(ScrollTrigger);

const ACTIVE_COLOR = new THREE.Color("#22C55E");
const FUTURE_COLOR = new THREE.Color("#80d4ff");
const DIM_COLOR = new THREE.Color("#53615b");

export default function FrameworkGalaxy({ frameworks = [], activeId }) {
  const hostRef = useRef(null);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return undefined;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(host.clientWidth, host.clientHeight);
    renderer.shadowMap.enabled = true;
    host.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, host.clientWidth / host.clientHeight, 0.1, 100);
    camera.position.set(0, 0.2, 13);

    const root = new THREE.Group();
    scene.add(root);

    const ambient = new THREE.AmbientLight("#cde9dd", 0.9);
    scene.add(ambient);

    const key = new THREE.DirectionalLight("#ffffff", 2);
    key.position.set(4, 7, 8);
    key.castShadow = true;
    scene.add(key);

    const nodeGeometry = new THREE.IcosahedronGeometry(0.34, 2);
    const activeGeometry = new THREE.OctahedronGeometry(0.52, 1);
    const materials = frameworks.slice(0, 50).map((framework) => {
      const color = framework.id === activeId ? ACTIVE_COLOR : framework.active ? FUTURE_COLOR : DIM_COLOR;
      return new THREE.MeshStandardMaterial({
        color,
        emissive: color,
        emissiveIntensity: framework.id === activeId ? 0.42 : framework.active ? 0.2 : 0.06,
        roughness: 0.38,
        metalness: 0.22
      });
    });

    const meshes = frameworks.slice(0, 50).map((framework, index) => {
      const angle = index * 0.72;
      const radius = 2.3 + index * 0.055;
      const z = (index % 9) * 0.42 - 1.8;
      const mesh = new THREE.Mesh(framework.id === activeId ? activeGeometry : nodeGeometry, materials[index]);
      mesh.position.set(Math.cos(angle) * radius, Math.sin(angle * 0.7) * 1.8, Math.sin(angle) * radius + z);
      mesh.rotation.set(index * 0.11, index * 0.06, index * 0.03);
      mesh.castShadow = true;
      root.add(mesh);
      return mesh;
    });

    const ringGeometry = new THREE.TorusGeometry(3.6, 0.01, 12, 160);
    const ringMaterial = new THREE.MeshBasicMaterial({ color: "#dfffee", transparent: true, opacity: 0.16 });
    const ring = new THREE.Mesh(ringGeometry, ringMaterial);
    ring.rotation.x = Math.PI / 2.8;
    root.add(ring);

    const starGeometry = new THREE.BufferGeometry();
    const starPositions = new Float32Array(900);
    for (let i = 0; i < starPositions.length; i += 3) {
      starPositions[i] = (Math.random() - 0.5) * 24;
      starPositions[i + 1] = (Math.random() - 0.5) * 14;
      starPositions[i + 2] = (Math.random() - 0.5) * 18;
    }
    starGeometry.setAttribute("position", new THREE.BufferAttribute(starPositions, 3));
    const stars = new THREE.Points(
      starGeometry,
      new THREE.PointsMaterial({ color: "#f6fff9", size: 0.018, transparent: true, opacity: 0.58 })
    );
    scene.add(stars);

    let frameId = 0;
    const pointer = { x: 0, y: 0 };
    const onPointerMove = (event) => {
      const rect = host.getBoundingClientRect();
      pointer.x = ((event.clientX - rect.left) / rect.width - 0.5) * 0.4;
      pointer.y = ((event.clientY - rect.top) / rect.height - 0.5) * 0.25;
    };

    const onResize = () => {
      renderer.setSize(host.clientWidth, host.clientHeight);
      camera.aspect = host.clientWidth / host.clientHeight;
      camera.updateProjectionMatrix();
    };

    host.addEventListener("pointermove", onPointerMove);
    window.addEventListener("resize", onResize);

    const timeline = gsap.timeline({
      scrollTrigger: {
        trigger: host,
        start: "top top",
        end: "bottom top",
        scrub: 1.1
      }
    });
    timeline.to(camera.position, { z: 8.2, y: 0.75, ease: "none" }, 0);
    timeline.to(root.rotation, { y: Math.PI * 0.62, x: -0.18, ease: "none" }, 0);

    const animate = () => {
      frameId = requestAnimationFrame(animate);
      root.rotation.y += 0.0028;
      root.rotation.x += (pointer.y - root.rotation.x) * 0.018;
      root.rotation.z += (pointer.x - root.rotation.z) * 0.018;
      ring.rotation.z += 0.004;
      stars.rotation.y -= 0.0007;
      meshes.forEach((mesh, index) => {
        mesh.rotation.x += 0.006 + index * 0.00003;
        mesh.rotation.y += 0.008;
      });
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(frameId);
      timeline.kill();
      ScrollTrigger.getAll().forEach((trigger) => trigger.kill());
      host.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("resize", onResize);
      renderer.dispose();
      nodeGeometry.dispose();
      activeGeometry.dispose();
      ringGeometry.dispose();
      ringMaterial.dispose();
      starGeometry.dispose();
      materials.forEach((material) => material.dispose());
      host.removeChild(renderer.domElement);
    };
  }, [frameworks, activeId]);

  return <div ref={hostRef} className="pointer-events-none absolute inset-0 min-h-[580px]" aria-hidden="true" />;
}
