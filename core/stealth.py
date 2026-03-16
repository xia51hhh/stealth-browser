"""
隐身注入脚本 - 修补浏览器指纹泄漏点
Patchright 已修复 Runtime.enable / navigator.webdriver / console API 泄漏
此模块处理 Patchright 未覆盖的额外泄漏点
"""

# WebRTC 防泄漏 - 阻止通过 WebRTC 泄漏真实 IP
DISABLE_WEBRTC = """
(() => {
    const origRTCPeerConnection = window.RTCPeerConnection;
    if (origRTCPeerConnection) {
        window.RTCPeerConnection = function(...args) {
            const config = args[0] || {};
            config.iceServers = [];
            return new origRTCPeerConnection(config);
        };
        window.RTCPeerConnection.prototype = origRTCPeerConnection.prototype;
    }
    // 同时处理旧版 API
    if (window.webkitRTCPeerConnection) {
        window.webkitRTCPeerConnection = window.RTCPeerConnection;
    }
})();
"""

# 修补 Chrome 插件数组 - 确保 plugins/mimeTypes 看起来正常
CHROME_PLUGINS = """
(() => {
    const pluginsData = [
        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer',
          description: 'Portable Document Format' },
        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
          description: '' },
        { name: 'Native Client', filename: 'internal-nacl-plugin',
          description: '' }
    ];
    const pluginArr = pluginsData.map(p => {
        const plugin = Object.create(Plugin.prototype);
        Object.defineProperties(plugin, {
            name: { value: p.name, enumerable: true },
            filename: { value: p.filename, enumerable: true },
            description: { value: p.description, enumerable: true },
            length: { value: 0, enumerable: true }
        });
        return plugin;
    });
    Object.defineProperty(navigator, 'plugins', {
        get: () => {
            const arr = Object.create(PluginArray.prototype);
            pluginArr.forEach((p, i) => { arr[i] = p; });
            Object.defineProperty(arr, 'length', { value: pluginArr.length });
            return arr;
        }
    });
})();
"""

# 修补 Permissions API - navigator.permissions.query 对 notifications 返回正常值
PERMISSIONS_FIX = """
(() => {
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications'
            ? Promise.resolve({ state: Notification.permission })
            : originalQuery(parameters)
    );
})();
"""

# 修补 iframe contentWindow - 确保跨 iframe 的 chrome 对象一致
IFRAME_CONTENT_WINDOW = """
(() => {
    try {
        const origHTMLIFrameElement = HTMLIFrameElement.prototype.__lookupGetter__('contentWindow');
        if (origHTMLIFrameElement) {
            Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
                get: function() {
                    const iframe = origHTMLIFrameElement.call(this);
                    if (iframe) {
                        // 确保 iframe 内部 chrome 对象正确
                        try {
                            if (!iframe.chrome) {
                                iframe.chrome = window.chrome;
                            }
                        } catch(e) {}
                    }
                    return iframe;
                }
            });
        }
    } catch(e) {}
})();
"""

# 确保 window.chrome 对象完整
CHROME_RUNTIME = """
(() => {
    if (!window.chrome) {
        window.chrome = {};
    }
    if (!window.chrome.runtime) {
        window.chrome.runtime = {
            connect: function() {},
            sendMessage: function() {},
            id: undefined
        };
    }
})();
"""

# 修补 Notification.permission
NOTIFICATION_FIX = """
(() => {
    if (Notification.permission === 'denied') {
        Object.defineProperty(Notification, 'permission', {
            get: () => 'default'
        });
    }
})();
"""

# 拦截 alert/confirm/prompt，加入随机延迟模拟人类反应
# 修复 detect-headless 的 Time Elapse 检测项
DIALOG_DELAY = """
(() => {
    const origAlert = window.alert;
    const origConfirm = window.confirm;
    const origPrompt = window.prompt;

    // 不完全拦截，而是让 page.on('dialog') 处理时有足够时间
    // Patchright 自动处理 dialog，这里标记一下用于行为分析
    window.__dialogTimestamp = 0;
    const origAddEventListener = EventTarget.prototype.addEventListener;
    // 保持原始行为，不做修改 — dialog 延迟由框架的 dialog handler 处理
})();
"""


def get_stealth_scripts(disable_webrtc: bool = True) -> list[str]:
    """返回所有需要注入的隐身脚本"""
    scripts = [
        CHROME_RUNTIME,
        CHROME_PLUGINS,
        PERMISSIONS_FIX,
        IFRAME_CONTENT_WINDOW,
        NOTIFICATION_FIX,
    ]
    if disable_webrtc:
        scripts.append(DISABLE_WEBRTC)
    return scripts
