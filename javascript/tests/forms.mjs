import assert from 'node:assert/strict';import {readFileSync}from'node:fs';import * as ui from'../dist/index.js';
const state=s=>s??{};
for(const c of JSON.parse(readFileSync(new URL('../../design/forms-cases.json',import.meta.url))).scenarios){
 const form=new ui.Form(c.fields.map(f=>({...f,state:state(f.state)})));
 for(const s of c.steps){if(s.focus){assert.ok(form.focus(s.focus));continue;}if(s.feedback){form.setFeedback(s.feedback,'',s.error);continue;}if(s.state){form.setState(s.state,state(s.value));continue;}
 const e=s.click?form.clickField(s.click,s.option??''):form.handle(s.action,s.text??'');assert.equal(e.kind,s.kind,c.name+JSON.stringify(s));assert.equal(e.text,s.event_text??'');if(s.missing)assert.deepEqual(e.data,s.missing);if(s.focused)assert.equal(form.focused,s.focused);
 for(const [key,attr]of[['choices','choice'],['pending','pending'],['open','open'],['checked','checked'],['display','value']])for(const [id,v]of Object.entries(s[key]??{}))assert.equal(form.fields.find(f=>f.id===id)[attr]??(typeof v==='boolean'?false:''),v);
 for(const[id,v]of Object.entries(s.values??{}))assert.equal(form.value(id),v);
 }
}
for(const fields of [[{id:'a'},{id:'a'}],[{id:''}],[{id:'a',kind:'bad'}],[{id:'a',kind:'select',open:true}],[{id:'a',options:[{id:'a'},{id:'a'}]}],[{id:'a',options:[{id:''}]}],[{id:'a',choice:'bad'}]])assert.throws(()=>new ui.Form(fields));
for(const theme of['dark','light','blackwhite'])for(const colors of['8','16','256','truecolor']){const f=new ui.Form([{id:'p',kind:'password',label:'Password',value:'秘密😀'},{id:'off',kind:'checkbox',state:{disabled:true}}]);for(let width=0;width<20;width++){const c=new ui.Canvas(24,8,new ui.Palette(theme,colors));f.draw(c,{x:2,y:1,width,height:6});assert.ok(!c.lines().join('').includes('秘密'));assert.equal(f.clickField('off').kind,'');if(c.cursor)assert.ok(c.cursor[0]>=2&&c.cursor[0]<2+width);}}
console.log('Forms shared validation/pending choices/states/passwords and all-palette clipped cursor passed');

{const f=new ui.Control({id:'a',value:'한'}),c=new ui.Canvas(10,6);f.draw(c,{x:1,y:1,width:8,height:4});assert.equal(f.click(-1,1,4).kind,'');assert.equal(f.click(8,1,4).kind,'');assert.equal(f.click(3,1,4).kind,'select');f.handle('insert','X');assert.equal(f.value('a'),'X한');}
