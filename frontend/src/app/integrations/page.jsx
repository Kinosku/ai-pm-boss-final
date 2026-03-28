"use client";

import { useEffect, useState } from "react";
import Sidebar from "../../components/Sidebar";
import Navbar from "../../components/Navbar";
import { integrationsApi } from "../../services/api";

const apps = [
  { name: "GitHub", key: "github" },
  { name: "Jira", key: "jira" },
  { name: "Slack", key: "slack" },
];

export default function IntegrationsPage() {
  const [connected, setConnected] = useState({});
  const [active, setActive] = useState(null);
  const [token, setToken] = useState("");

  // 🔥 FETCH CONNECTED SERVICES
  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await integrationsApi.list();
        const map = {};
        res.data.forEach((i) => (map[i.type] = true));
        setConnected(map);
      } catch (err) {
        console.error(err);
      }
    };
    fetch();
  }, []);

  // 🔥 CONNECT
  const connect = async () => {
    try {
      await integrationsApi.connect({
        type: active,
        token,
      });

      setConnected((prev) => ({ ...prev, [active]: true }));
      setActive(null);
      setToken("");
    } catch (err) {
      console.error(err);
    }
  };

  // 🔥 DISCONNECT
  const disconnect = async (type) => {
    try {
      await integrationsApi.disconnect(type);
      setConnected((prev) => ({ ...prev, [type]: false }));
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex-1">
        <Navbar title="Integrations" />

        <div className="p-6">
          <h1 className="text-2xl font-bold mb-6">Integrations</h1>

          <div className="grid md:grid-cols-3 gap-5">
            {apps.map((app) => (
              <div
                key={app.key}
                className="p-5 rounded-xl border bg-white/5"
              >
                <h2 className="font-semibold">{app.name}</h2>

                <p className="text-sm text-gray-400 mt-2">
                  Connect your {app.name} account
                </p>

                <div className="mt-4">
                  {connected[app.key] ? (
                    <button
                      onClick={() => disconnect(app.key)}
                      className="px-4 py-2 bg-red-500 rounded"
                    >
                      Disconnect
                    </button>
                  ) : (
                    <button
                      onClick={() => setActive(app.key)}
                      className="px-4 py-2 bg-primary rounded"
                    >
                      Connect
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* MODAL */}
          {active && (
            <div className="fixed inset-0 flex items-center justify-center bg-black/60">
              <div className="bg-black p-6 rounded w-[350px]">
                <h2 className="mb-3">Connect {active}</h2>

                <input
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="Enter token"
                  className="w-full p-2 border mb-3"
                />

                <button
                  onClick={connect}
                  className="px-3 py-2 bg-green-500 rounded"
                >
                  Connect
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}