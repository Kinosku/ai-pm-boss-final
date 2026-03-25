export default function Home() {
  return (
    <div className="bg-[#06090f] text-white min-h-screen relative overflow-x-hidden">

      {/* Background Layers */}
      <div className="fixed inset-0 noise-overlay z-0"></div>
      <div className="fixed inset-0 ambient-glow z-0"></div>

      <div className="relative z-10 flex flex-col min-h-screen">

        {/* HEADER */}
        <header className="flex items-center justify-between px-12 py-8 max-w-[1440px] mx-auto w-full backdrop-blur-md sticky top-0 z-50">
          <div className="flex items-center gap-3">
            <div className="size-10 text-green-400 rotate-45 bg-green-400"></div>
            <h1 className="text-2xl font-bold">
              AI PM <span className="velocity-gradient-text">BOSS</span>
            </h1>
          </div>

          <button className="flex items-center gap-2 text-gray-400 hover:text-white">
            ← Return to Main
          </button>
        </header>

        {/* MAIN */}
        <main className="flex-1 flex flex-col items-center justify-center p-8 lg:p-12">

          <div className="w-full max-w-[1200px] flex flex-col gap-16">

            {/* LOGIN CARD */}
            <div className="flex flex-col lg:flex-row rounded-2xl overflow-hidden shadow-2xl bg-[#181c22] ghost-border">

              {/* LEFT */}
              <div className="w-full lg:w-1/2 relative min-h-[500px] hidden lg:flex flex-col justify-end p-16">
                <div className="absolute inset-0 bg-black/60"></div>

                <div className="relative z-10">
                  <span className="text-xs tracking-widest text-green-400 mb-6 uppercase font-mono">
                    SYSTEM READY
                  </span>

                  <h2 className="text-6xl font-bold mb-4">
                    Welcome <span className="velocity-gradient-text">Back</span>
                  </h2>

                  <p className="text-gray-400 text-lg max-w-sm">
                    Resume your AI-powered workflow.
                  </p>
                </div>
              </div>

              {/* RIGHT */}
              <div className="w-full lg:w-1/2 p-12 lg:p-20 bg-[#1c2026]/70 backdrop-blur-sm">

                <h3 className="text-3xl font-bold mb-6">Sign In</h3>

                <form className="space-y-8">

                  <input
                    type="email"
                    placeholder="name@company.ai"
                    className="w-full px-5 py-5 rounded-xl bg-[#0b0e14] ring-1 ring-white/10 focus:ring-green-400/40 outline-none"
                  />

                  <input
                    type="password"
                    placeholder="••••••••"
                    className="w-full px-5 py-5 rounded-xl bg-[#0b0e14] ring-1 ring-white/10 focus:ring-green-400/40 outline-none"
                  />

                  <button className="w-full velocity-gradient-bg text-black font-bold py-5 rounded-xl hover:shadow-[0_0_30px_rgba(0,255,180,0.4)] transition-all">
                    Authenticate System
                  </button>
                </form>
              </div>
            </div>

            {/* NODES */}
            <div className="grid md:grid-cols-3 gap-8">

              {["Strategy Suite", "Delivery Core", "Agent Terminal"].map((item, i) => (
                <div key={i} className="p-8 rounded-2xl bg-[#181c22] ghost-border node-glow cursor-pointer">
                  <h4 className="font-bold text-lg mb-3">{item}</h4>
                  <p className="text-sm text-gray-400">
                    Advanced system access module.
                  </p>
                </div>
              ))}

            </div>

          </div>
        </main>

        {/* FOOTER */}
        <footer className="p-12 max-w-[1440px] mx-auto w-full flex justify-between border-t border-white/5 text-xs text-gray-500">
          <span>© 2024 AI PM BOSS</span>
          <span>SYSTEM STATUS: NOMINAL</span>
        </footer>

      </div>
    </div>
  );
}