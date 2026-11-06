import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {Text,Form,Canvas} from '../dist/index.js';
for(const c of JSON.parse(readFileSync(new URL('../../design/controls-cases.json',import.meta.url))).text){
 const t=new Text(c.text,{readOnly:c.read_only,secret:c.secret,multiline:!c.single_line});
 for(const op of c.ops){const e=t.handle(op.action,op.text??'');assert.equal(e.kind,op.kind,c.name);assert.equal(e.text,op.event_text??'');}
 assert.equal(t.value,c.expected);assert.equal(t.cursor,c.cursor);
}
const t=new Text('a\r\n한é😀');t.selectBytes(3,9);assert.deepEqual(t.selectionBytes(),[3,9]);assert.throws(()=>t.replaceBytes(4,9,'bad'));assert.equal(t.value,'a\r\n한é😀');t.replaceBytes(3,9,'[red]\r\n');assert.equal(t.value,'a\r\n[red]\r\n😀');t.handle('undo');assert.equal(t.value,'a\r\n한é😀');
const f=new Form([{id:'p',kind:'password',value:'秘密😀'}]);assert.equal(f.fields[0].value,'***');assert.equal(f.value('p'),'秘密😀');assert.ok(!JSON.stringify(f.inputs.get('p')).includes('秘密'));
const n=new Text('한😀x',{multiline:false});n.select(0,2);for(let width=1;width<9;width++){const c=new Canvas(12,4);c.write(0,0,'OUTSIDE');n.draw(c,{x:3,y:1,width,height:1});assert.equal(c.lines()[0].trim(),'OUTSIDE');if(c.cursor)assert.ok(c.cursor[0]>=3&&c.cursor[0]<3+width);}
console.log('Text shared editing, raw UTF-8 ranges, password and clipped real cursor passed');
