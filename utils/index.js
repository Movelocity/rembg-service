/*
Gradio 功能植入

包括:
- 展示短消息 showToast(字符串, 持续毫秒)
- 植入亮暗切换按钮，在页面底部。页面加载时马上切换到用户之前的选择
- 解决非https网页无法自动复制的问题，为 Textbox 组件添加 with_copy_btn 样式类即可注入复制按钮

新加入的配置函数请加入到 setupTasks 中。
*/

const toastElem = document.createElement('div');
toastElem.id = 'toast';
const showToast = (message, duration) => {
  toastElem.innerHTML = message;
  toastElem.className = "show";
  setTimeout(() => {
    toastElem.className = toastElem.className.replace("show", "");
  }, duration + 100); // Add a small buffer to ensure the CSS animation completes
}
const setupToast = ()=>{
  let bodyElement = document.body;
  bodyElement.insertBefore(toastElem, bodyElement.firstChild);
}
// Increments the toggle count stored in local storage
const toggleCount = () => {
  // Retrieve the current toggle count, defaulting to 0 if it doesn't exist
  let toggleCount = parseInt(localStorage.getItem('toggleCount') || '0');
  toggleCount++;
  localStorage.setItem('toggleCount', toggleCount.toString());
}
// Applies the dark theme based on the current toggle count
const applyTheme = () => {
  const toggleCount = parseInt(localStorage.getItem('toggleCount') || '0');
  // If the toggle count is odd, toggle the theme
  if (toggleCount % 2 !== 0) {
    document.body.classList.toggle('dark');
  }
}
const setupLightDarkSwitch = () => {
  const footer = document.getElementsByTagName('footer')[0];
  const lightDarkSwitch = document.createElement('div');
  lightDarkSwitch.className = 'text_btn';
  lightDarkSwitch.innerText = "亮/暗主题切换";

  lightDarkSwitch.addEventListener('click', (e) => {
    document.body.classList.toggle('dark');
    toggleCount();
  });
  footer.appendChild(lightDarkSwitch);
}

const bindCopyBtn = ()=>{
  const text_components = document.querySelectorAll(".with_copy_btn");
  text_components.forEach((component)=>{
    const text_elem = component.querySelector('textarea');
    const copy_btn = document.createElement('div');
    copy_btn.innerText = 'copy'
    copy_btn.classList.add('copy_btn', 'text_btn')
    copy_btn.addEventListener('click', (e)=>{
      console.log('copying');
      // 浏览器禁止了非https页面使用navigator.clipboard, 
      // 可以用这个方式绕过限制，写入剪贴板
      const textArea = document.createElement("textarea");
      textArea.style.position = 'fixed';
      // textArea.style.visibility = "hidden";  
      // 不显示，但是占用 DOM, 经测试隐藏了就无法选中，无法copy
      textArea.value = text_elem.value;
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      try {
        document.execCommand("copy");
        showToast("copied", 2000);
      } catch (error) {
        showToast("not copied", 2000);
      }
      document.body.removeChild(textArea);
    })
    component.appendChild(copy_btn);
  })
}

const customAccordion = ()=>{
  // 绑定方法 with gr.Accordion('尺寸预设 (pixel)', open=False, elem_classes='hide_accordion_on_click'):
  const accordion_components = document.querySelectorAll(".hide_accordion_on_click");
  accordion_components.forEach((component)=>{
    const btn = component.querySelector('.label-wrap');
    component.querySelectorAll('.table').forEach((cell)=>{
      cell.addEventListener('click', (e)=>{
        btn.click();
        console.log('is accordion hidden?')
      })
    })
  })
}

// 监听 DOM 变更的函数，以便在特定元素加载完毕后执行任务
function whenElementReady(selector, callback) {
  let observer = new MutationObserver(mutations => {
    if (document.querySelector(selector)) {
      observer.disconnect(); // 停止观察
      callback();
    }
  });
  observer.observe(document.body, {
    childList: true, // 监听子元素的变化
    subtree: true   // 监听后代节点的变化
  });
}


// 在这里列举需要注入到 gradio 页面的函数
const instantTasks = [
  applyTheme,
  setupLightDarkSwitch,
]
// gradio 部分元素渲染得比较慢，需要进一步延时等待加载
const lazyTasks = [
  bindCopyBtn,
  customAccordion,
  setupToast,
]
document.addEventListener('DOMContentLoaded', ()=>{
  // 等待页面底部组件渲染后，注入页面优化脚本
  whenElementReady('footer > .built-with', ()=>{instantTasks.forEach((t)=>{t()})});
  setTimeout(()=>{
    lazyTasks.forEach((t)=>{t()});
  }, 500)
});

