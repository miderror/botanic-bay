import cors from "cors";
import express from "express";

const app = express();
const PORT = 9229;

// Настройка middleware
app.use(cors());
app.use(express.json());

// Обработчик логов
app.post("/log", (req, res) => {
  const { type, message, timestamp } = req.body;

  switch (type) {
    case "log":
      console.log("[BROWSER]:", ...message);
      break;
    case "warn":
      console.warn("[BROWSER]:", ...message);
      break;
    case "error":
      console.error("[BROWSER]:", ...message);
      break;
  }

  res.json({ status: "ok", timestamp });
});

// Запуск сервера
app.listen(PORT, () => {
  console.log(`Dev log server running at http://localhost:${PORT}`);
});
