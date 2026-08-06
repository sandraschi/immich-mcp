import { AppLayout } from "@/components/layout/app-layout";
import { Albums } from "@/pages/albums";
import { Chat } from "@/pages/chat";
import { Dashboard } from "@/pages/dashboard";
import { Help } from "@/pages/help";
import { Libraries } from "@/pages/libraries";
import { Logger } from "@/pages/logger";
import { Map as MapPage } from "@/pages/map";
import { People } from "@/pages/people";
import { Photos } from "@/pages/photos";
import { Settings } from "@/pages/settings";
import { Tools } from "@/pages/tools";
import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";

function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/photos" element={<Photos />} />
          <Route path="/albums" element={<Albums />} />
          <Route path="/people" element={<People />} />
          <Route path="/map" element={<MapPage />} />
          <Route path="/libraries" element={<Libraries />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/tools" element={<Tools />} />
          <Route path="/logger" element={<Logger />} />
          <Route path="/help" element={<Help />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </Router>
  );
}

export default App;
