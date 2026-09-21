import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1", // Oder eine spezifische IP-Adresse
    port: 5173, // Wähle deinen gewünschten Port
    strictPort: true, // Falls der Port bereits belegt ist, schlägt der Start fehl
  },
});
