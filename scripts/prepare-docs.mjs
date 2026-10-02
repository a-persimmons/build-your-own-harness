import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
const root=path.resolve(import.meta.dirname,'..');
const output=path.join(root,'.book-docs');
const sourcePaths=['README.md','build-your-own-harness.md','ARCHITECTURE.md','SPEC.md','CLAUDE.md',...fs.readdirSync(root).filter(p=>/^layer-\d+-/.test(p)&&fs.existsSync(path.join(root,p,'README.md'))).sort().map(p=>p+'/README.md')];
const manifest=JSON.parse(fs.readFileSync(path.join(root,'i18n/manifest.json'),'utf8'));
const route=p=>p.replace(/(^|\/)README\.md$/,'$1index.md');
const sha=text=>createHash('sha256').update(text).digest('hex');
const codeBlocks=text=>[...text.matchAll(/^```[^\n]*\n[\s\S]*?^```[^\S\n]*$/gm)].map(m=>m[0]);
fs.rmSync(output,{recursive:true,force:true});fs.mkdirSync(output,{recursive:true});
const links=new Map(sourcePaths.map(p=>[p,route(p)]));
for(const p of sourcePaths) if(p.endsWith('/README.md')) links.set(path.posix.dirname(p),route(p));
const notes={
 zh:'::: info 阅读说明\n当前仓库已实现第 1–4 层；第 5–17 层为规划。本页是英文原文的中文翻译，代码与命令保持原样。原文中的时效性信息与作者观点按原意保留，不代表已重新核验。\n:::\n',
 en:'::: info Implementation status\nLayers 1–4 have runnable implementations. Layers 5–17 are a roadmap, not completed tutorials. This reading site preserves the upstream English text.\n:::\n'
};
for(const source of sourcePaths){
 const english=fs.readFileSync(path.join(root,source),'utf8');
 const translated=fs.readFileSync(path.join(root,'i18n/zh',source),'utf8');
 if(manifest[source]!==sha(english))throw new Error(`English source changed: review the Chinese translation and update i18n/manifest.json for ${source}`);
 if(JSON.stringify(codeBlocks(english))!==JSON.stringify(codeBlocks(translated)))throw new Error(`Code blocks differ in translation: ${source}`);
 for(const language of ['zh','en']){
  const prefix=language==='en'?'/en/':'/';
  let text=language==='zh'?translated:english;
  const resolveLink=(href)=>{
   if(/^(?:[a-z]+:|\/\/|#)/i.test(href))return href;
   const [raw,anchor]=href.split('#');
   const file=path.posix.normalize(path.posix.join(path.posix.dirname(source),decodeURIComponent(raw))).replace(/\/$/,'');
   if(file==='layer-05-storage')return prefix+'build-your-own-harness#layer-5';
   const target=links.get(file);
   if(target)return prefix+target.replace(/index\.md$/,'').replace(/\.md$/,'')+(anchor?'#'+anchor:'');
   return 'https://github.com/a-persimmons/build-your-own-harness/blob/main/'+file+(anchor?'#'+anchor:'');
  };
  let fence=false; let headingIndex=0;
  text=text.split('\n').map(line=>{
   if(/^\s*```/.test(line)){fence=!fence;return line;}
   if(fence)return line;
   line=line.replace(/\]\(([^\s)]+)\)/g,(_,url)=>']('+resolveLink(url)+')');
   line=line.replace(/\[\[([^\]]+)\]\]/g,(_,name)=>'`'+name+'`');
   if(/^#{1,6} /.test(line)){
    const layer=source==='build-your-own-harness.md'?line.match(/^### (?:Layer |第 )(\d+)/):null;
    line+=' {#'+(layer?'layer-'+layer[1]:'section-'+(++headingIndex))+'}';
   }
   return line;
  }).join('\n');
  const sourceUrl='https://github.com/a-persimmons/build-your-own-harness/blob/main/'+source;
  const notice=notes[language]+(source==='build-your-own-harness.md'?(language==='zh'?'\n原文的双链笔记未包含在此仓库中，以下以等宽文本保留笔记名称。\n':'\nThe upstream wiki-linked notes are not included in this repository; their names are shown as inline code below.\n'):'');
  text=text.replace(/^(# .+)$/m,'$1\n\n'+notice+'\n'+(language==='zh'?'[查看英文源文件]':'[View English source]')+'('+sourceUrl+')');
  const dest=path.join(output,language==='en'?'en':'',route(source));
  fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,text);
 }
}
fs.cpSync(path.join(root,'.vitepress'),path.join(output,'.vitepress'),{recursive:true});
console.log(`Prepared ${sourcePaths.length*2} bilingual pages; code blocks and translation source revisions verified.`);
