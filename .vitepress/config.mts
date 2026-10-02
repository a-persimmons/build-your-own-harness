import {defineConfig} from 'vitepress';
const repo='https://github.com/a-persimmons/build-your-own-harness';
const layers=['layer-01-api-shell','layer-02-tools','layer-03-context','layer-04-memory'];
function sidebar(en=false){const p=en?'/en/':'/';return [
 {text:en?'Start here':'开始阅读',items:[{text:en?'Introduction & quickstart':'项目介绍与快速开始',link:p},{text:en?'17-layer roadmap':'17 层完整路线图',link:p+'build-your-own-harness'}]},
 {text:en?'Runnable tutorials · Layers 1–4':'可运行教程 · 第 1–4 层',items:layers.map((s,i)=>({text:(en?['1 · API Shell & CLI','2 · Tools & Function Calling','3 · Context Management','4 · Memory']:['第 1 层 · API 外壳与命令行','第 2 层 · 工具与函数调用','第 3 层 · 上下文管理','第 4 层 · 长期记忆'])[i],link:p+s+'/'}))},
 {text:en?'Project documentation':'项目文档',collapsed:true,items:[{text:en?'Architecture':'架构说明',link:p+'ARCHITECTURE'},{text:en?'Specification':'项目规格',link:p+'SPEC'},{text:en?'Development conventions':'开发规范',link:p+'CLAUDE'}]}
]}
export default defineConfig({
 base:'/build-your-own-harness/', title:'Build Your Own Harness', description:'从零构建 Agent Harness：中英双语分层实战教程',
 locales:{
  root:{label:'简体中文',lang:'zh-CN',themeConfig:{nav:[{text:'开始学习',link:'/layer-01-api-shell/'},{text:'完整路线',link:'/build-your-own-harness'}],sidebar:sidebar(),outline:{label:'本页目录',level:[2,3]},docFooter:{prev:'上一节',next:'下一节'},sidebarMenuLabel:'章节目录',returnToTopLabel:'返回顶部',darkModeSwitchLabel:'外观',langMenuLabel:'切换语言',footer:{message:'中英双语阅读镜像 · 英文内容来自原仓库，中文为辅助译文'}}},
  en:{label:'English',lang:'en',themeConfig:{nav:[{text:'Start learning',link:'/en/layer-01-api-shell/'},{text:'Roadmap',link:'/en/build-your-own-harness'}],sidebar:sidebar(true),outline:{label:'On this page',level:[2,3]},footer:{message:'Bilingual reading mirror · English source preserved; Chinese translation provided for learning'}}}
 },
 themeConfig:{socialLinks:[{icon:'github',link:repo}],search:{provider:'local',options:{miniSearch:{options:{tokenize:(text)=>Array.from(new Intl.Segmenter('zh-CN',{granularity:'word'}).segment(text)).filter(s=>s.isWordLike).map(s=>s.segment)}},locales:{root:{translations:{button:{buttonText:'搜索教程',buttonAriaLabel:'搜索教程'},modal:{noResultsText:'没有找到相关内容',resetButtonTitle:'清除搜索',footer:{selectText:'选择',navigateText:'切换',closeText:'关闭'}}}}}}}}
});
