import tailwindcss from "@tailwindcss/vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";
import type { Connect } from "vite";
import { defineConfig, loadEnv } from "vite";
import vueDevTools from "vite-plugin-vue-devtools";

// Создаем отдельную функцию для обработки логов
function createLogHandler(): Connect.NextHandleFunction {
  return function logHandler(req, res, next) {
    if (req.url === "/log" && req.method === "POST") {
      let body = "";
      req.on("data", (chunk) => {
        body += chunk.toString();
      });
      req.on("end", () => {
        try {
          const logData = JSON.parse(body);
          switch (logData.type) {
            case "log":
              console.log("[BROWSER]:", ...logData.message);
              break;
            case "warn":
              console.warn("[BROWSER]:", ...logData.message);
              break;
            case "error":
              console.error("[BROWSER]:", ...logData.message);
              break;
          }
          res.statusCode = 200;
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ status: "ok" }));
        } catch (e) {
          console.error("Error processing log:", e);
          res.statusCode = 500;
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ error: "Failed to process log" }));
        }
      });
    } else {
      next();
    }
  };
}

// Определяем директорию, где лежит .env (на уровень выше, т.е. в frontend)
const envDir = fileURLToPath(new URL("./", import.meta.url));
// Корневая директория проекта – там, где находится index.html (frontend/app)
const projectRoot = fileURLToPath(new URL("./", import.meta.url));

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, envDir, "");
  const allowedHost = env.VITE_NGROK_URL ? env.VITE_NGROK_URL.replace(/^https?:\/\//, "") : "";

  console.log("envDir: ", envDir);
  console.log("projectRoot: ", projectRoot);
  console.log("Allowed host: ", allowedHost);

  return {
    plugins: [vue(), vueDevTools(), tailwindcss()],
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
    assetsInclude: ["**/*.html"],
    server: {
      host: "0.0.0.0",
      port: 5173,
      strictPort: true,
      cors: true,
      proxy: {
        "/media": {
          target: "http://localhost:80",
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/media/, "/media"),
          configure: (proxy) => {
            proxy.on("proxyReq", (proxyReq, req) => {
              console.log("Proxying media request:", {
                path: req.url,
                target: "http://localhost:8000",
              });
            });
          },
        },
      },
      hmr: true,
      allowedHosts: allowedHost ? [allowedHost, env.API_HOST] : [],
      // Добавим поддержку шрифтов
      assetsInclude: ["**/*.ttf", "**/*.woff", "**/*.woff2"],
      // Используем configureServer для настройки middleware
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      configureServer(server: any) {
        // Добавляем обработчик логов перед всеми остальными middleware
        server.middlewares.use(createLogHandler());
      },
    },
    test: {
      environment: "jsdom",
      globals: true,
      setupFiles: ["./tests/setup.ts"],
      include: ["**/*.{test,spec}.{js,ts,jsx,tsx}"],
    },
  };
});
