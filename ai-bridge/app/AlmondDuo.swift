import Cocoa
import WebKit

final class AppDelegate: NSObject, NSApplicationDelegate, WKNavigationDelegate, WKDownloadDelegate {
    var window: NSWindow!
    var web: WKWebView!
    var service: Process?
    var poll: Timer?
    var launchDirectory: URL!
    var host: String = ""
    var attempts = 0

    func applicationDidFinishLaunching(_ notification: Notification) {
        let main = NSMenu()
        let applicationItem = NSMenuItem()
        let applicationMenu = NSMenu()
        applicationMenu.addItem(withTitle: "About Almond Duo", action: #selector(about), keyEquivalent: "")
        applicationMenu.addItem(NSMenuItem.separator())
        applicationMenu.addItem(withTitle: "Quit Almond Duo", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        applicationItem.submenu = applicationMenu
        main.addItem(applicationItem)
        let edit = NSMenuItem()
        edit.title = "Edit"
        let menu = NSMenu(title: "Edit")
        for (title, action, key) in [("Undo", "undo:", "z"), ("Redo", "redo:", "Z"), ("Cut", "cut:", "x"), ("Copy", "copy:", "c"), ("Paste", "paste:", "v"), ("Select All", "selectAll:", "a")] {
            menu.addItem(withTitle: title, action: Selector(action), keyEquivalent: key)
        }
        edit.submenu = menu
        main.addItem(edit)
        NSApp.mainMenu = main
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 1220, height: 830), styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false)
        window.title = "Almond Duo"
        window.minSize = NSSize(width: 760, height: 560)
        window.center()
        window.setFrameAutosaveName("AlmondDuoMainWindow")
        web = WKWebView(frame: .zero)
        web.navigationDelegate = self
        window.contentView = web
        web.loadHTMLString("<html><body style='background:#f6f3ed;color:#302b26;font:20px -apple-system;padding:70px'><h1>Almond Duo</h1><p>Opening your shared workspace…</p></body></html>", baseURL: nil)
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        startService()
    }

    @objc func about() {
        let alert = NSAlert()
        alert.messageText = "Almond Duo"
        alert.informativeText = "One prompt. Two collaborators.\nA local workspace for Claude Code and Codex."
        alert.runModal()
    }

    func startService() {
        do {
            guard let resources = Bundle.main.resourceURL else { throw NSError(domain: "Almond", code: 1) }
            let settings = try JSONSerialization.jsonObject(with: Data(contentsOf: resources.appendingPathComponent("runtime.json"))) as! [String: String]
            launchDirectory = FileManager.default.temporaryDirectory.appendingPathComponent("almond-duo-" + UUID().uuidString)
            try FileManager.default.createDirectory(at: launchDirectory, withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700])
            let project = resources.appendingPathComponent("project")
            let process = Process()
            process.executableURL = URL(fileURLWithPath: settings["python"]!)
            process.arguments = [project.appendingPathComponent("ai-bridge/app/server.py").path, "--project", project.path, "--ready", launchDirectory.appendingPathComponent("ready.json").path]
            var environment = ProcessInfo.processInfo.environment
            environment["PATH"] = NSHomeDirectory() + "/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
            process.environment = environment
            let logs = FileManager.default.urls(for: .libraryDirectory, in: .userDomainMask)[0].appendingPathComponent("Logs/Almond Duo")
            try FileManager.default.createDirectory(at: logs, withIntermediateDirectories: true)
            let log = logs.appendingPathComponent("app.log")
            FileManager.default.createFile(atPath: log.path, contents: nil)
            let handle = try FileHandle(forWritingTo: log)
            process.standardOutput = handle
            process.standardError = handle
            service = process
            try process.run()
            poll = Timer.scheduledTimer(withTimeInterval: 0.15, repeats: true) { [weak self] timer in
                guard let self = self else { return }
                self.attempts += 1
                if let bytes = try? Data(contentsOf: self.launchDirectory.appendingPathComponent("ready.json")),
                   let data = try? JSONSerialization.jsonObject(with: bytes) as? [String: Any],
                   let raw = data["url"] as? String, let url = URL(string: raw) {
                    self.host = "127.0.0.1:" + String(url.port!)
                    timer.invalidate()
                    self.web.load(URLRequest(url: url))
                } else if self.attempts > 200 || !process.isRunning {
                    timer.invalidate()
                    self.fail("The local service could not start. Check ~/Library/Logs/Almond Duo/app.log. Your conversations are retained.")
                }
            }
        } catch { fail("Could not open the local workspace: \(error.localizedDescription)") }
    }

    func fail(_ message: String) {
        let alert = NSAlert()
        alert.messageText = "Almond Duo needs attention"
        alert.informativeText = message
        alert.runModal()
    }

    func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        if action.shouldPerformDownload { decisionHandler(.download); return }
        guard let url = action.request.url else { decisionHandler(.cancel); return }
        if url.scheme == "about" || (url.host == "127.0.0.1" && "127.0.0.1:\(url.port ?? 0)" == host) { decisionHandler(.allow); return }
        if action.navigationType == .linkActivated && ["https", "http"].contains(url.scheme ?? "") { NSWorkspace.shared.open(url) }
        decisionHandler(.cancel)
    }
    func webView(_ webView: WKWebView, navigationAction: WKNavigationAction, didBecome download: WKDownload) { download.delegate = self }
    func download(_ download: WKDownload, decideDestinationUsing response: URLResponse, suggestedFilename: String, completionHandler: @escaping (URL?) -> Void) {
        let panel = NSSavePanel()
        panel.nameFieldStringValue = suggestedFilename
        panel.beginSheetModal(for: window) { answer in completionHandler(answer == .OK ? panel.url : nil) }
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
    func applicationWillTerminate(_ notification: Notification) {
        poll?.invalidate()
        if let process = service, process.isRunning { process.terminate() }
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()
