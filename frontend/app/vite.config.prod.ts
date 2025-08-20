/**
 * Настройки Vite для продкшен-сборки приложения
 * Подставляется вместо vite.config.ts в Dockerfile для продакшена
 */
import tailwindcss from "@tailwindcss/vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";
import type { Connect } from "vite";
import { defineConfig, loadEnv } from "vite";

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

export default defineConfig(({ mode, command }) => {
  // Определяем директорию, где лежит .env (на уровень выше, т.е. в frontend)
  const envDir = fileURLToPath(new URL("../", import.meta.url));

  // Загружаем переменные окружения
  const env = loadEnv(mode, envDir, "");

  console.log("Build mode:", mode, "command:", command);
  console.log("envDir:", envDir);
  console.log("VITE_YANDEX_MAPS_API_KEY:", env.VITE_YANDEX_MAPS_API_KEY);

  return {
    plugins: [vue(), tailwindcss()],
    define: {
      // Явно определяем переменные окружения для времени выполнения
      "import.meta.env.VITE_YANDEX_MAPS_API_KEY": JSON.stringify(env.VITE_YANDEX_MAPS_API_KEY),
      "import.meta.env.VITE_API_URL": JSON.stringify(env.VITE_API_URL),
      "import.meta.env.VITE_TELEGRAM_BOT_NAME": JSON.stringify(env.VITE_TELEGRAM_BOT_NAME),
      "import.meta.env.VITE_TG_DEV_MODE": JSON.stringify(env.VITE_TG_DEV_MODE),
    },
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
    build: {
      outDir: "dist",
      emptyOutDir: true,
      assetsDir: "assets",
      // TODO: по окончании разработки нужно будет включить минификацию и отключить sourcemap
      minify: false,
      sourcemap: true,
      rollupOptions: {
        input: {
          app: fileURLToPath(new URL("./index.html", import.meta.url)),
        },
        output: {
          entryFileNames: "assets/[name].[hash].js",
          chunkFileNames: "assets/[name].[hash].js",
          assetFileNames: (assetInfo) => {
            if (!assetInfo.name) return "assets/[name].[hash][extname]";
            const info = assetInfo.name.split(".");
            const ext = info[info.length - 1];
            if (/\.(gif|jpe?g|png|svg)$/i.test(assetInfo.name)) {
              return `images/[name].[hash].${ext}`;
            }
            return `assets/[name].[hash].${ext}`;
          },
        },
      },
    },
    server: {
      host: "0.0.0.0",
      port: 80,
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
                target: "http://localhost:80",
              });
            });
          },
        },
      },
      assetsInclude: ["**/*.ttf", "**/*.woff", "**/*.woff2"],
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      configureServer(server: any) {
        server.middlewares.use(createLogHandler());
      },
    },
  };
});
