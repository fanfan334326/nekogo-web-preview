// Loaded before Flutter so an early browser install event is not lost.
(() => {
  let pendingPrompt = null;
  let installed = false;
  let prompting = false;
  const standalone = () => installed ||
    window.matchMedia('(display-mode: standalone)').matches ||
    window.navigator.standalone === true;

  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault();
    pendingPrompt = event;
  });
  window.addEventListener('appinstalled', () => {
    installed = true;
    pendingPrompt = null;
  });

  window.nekogoShortcutInstalled = standalone;
  window.nekogoShortcutGuide = () => {
    const nav = window.navigator;
    const ua = nav.userAgent;
    // iPadOS may identify as a Mac when requesting desktop websites.
    const appleMobile = /iPhone|iPad|iPod/i.test(ua) ||
      (/Macintosh|MacIntel/i.test(`${ua} ${nav.platform}`) && nav.maxTouchPoints > 1);
    if (appleMobile) {
      return '在 Safari 中打开本页，然后：\n\n1. 点浏览器工具栏的“分享”（方框向上箭头）；如果没看到，先点“更多”。\n2. 选择“添加到主屏幕”；如果没看到，向下滚动或点“编辑操作”查找。\n3. 如果有“作为网页 App 打开”，保持开启，再点“添加”。\n\niPhone 和 iPad 的分享按钮位置可能不同。若在微信等应用内，请先用 Safari 打开本页。';
    }
    if (/Android/i.test(ua)) {
      return '点浏览器右上角的菜单，选择“添加到主屏幕”或“安装应用”，再按提示确认。\n\n如果没有这些选项，请用 Chrome 打开本页后再试。';
    }
    return '在浏览器菜单中查找“安装应用”或“创建快捷方式”。\n\n如果你用的是 Mac 上的 Safari，可在“文件”菜单中选择“添加到程序坞”。手机和平板请在设备上打开本页后添加。';
  };

  window.nekogoRequestShortcut = async () => {
    if (standalone()) return 'installed';
    if (prompting) return 'dismissed';
    if (!pendingPrompt) return 'manual';
    const event = pendingPrompt;
    pendingPrompt = null; // A browser install event can only be used once.
    prompting = true;
    try {
      await event.prompt();
      const choice = await event.userChoice;
      return choice.outcome === 'accepted' ? 'accepted' : 'dismissed';
    } catch (_) {
      return 'manual';
    } finally {
      prompting = false;
    }
  };
})();
