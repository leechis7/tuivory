import json,unittest
from pathlib import Path
from tuivory import *
ROOT=Path(__file__).resolve().parents[2]
CASES=sum([json.loads((ROOT/'design'/name).read_text())['cases']for name in ['syntax-cases.json','syntax-extra-cases.json']],[])
class Syntax(unittest.TestCase):
 def test_shared_tokens(self):
  analyzer=SQLAnalyzer()
  for f in CASES:
   with self.subTest(case=f['name']):
    a=analyzer.analyze_syntax(f['source'],SyntaxRequest(f['language'],f['dialect']));a.validate(f['source']);self.assertEqual([vars(t)for t in a.tokens],f['tokens'])
  with self.assertRaises(ValueError):analyzer.analyze_syntax('x',SyntaxRequest('python',''))
 def test_cached_callbacks_and_failed_refresh_preserve_editor(self):
  calls=[];fail=[False];analyzer=SQLAnalyzer()
  def analyze(text,request):
   calls.append(text)
   if fail[0]:raise ValueError('sample failure')
   return analyzer.analyze_syntax(text,request)
  d=TextDocument.editor('SELECT 1');d.set_syntax_analyzer(analyze);self.assertEqual(len(calls),1)
  for theme in ['dark','light','blackwhite']:
   for colors in ['8','16','256','truecolor']:d.draw(Canvas(40,4,Palette(theme,colors)),Rect(0,0,40,4))
  d.handle('scroll_down');d.layout(12,2);self.assertEqual(len(calls),1)
  d.handle('insert',' ');d.layout(40,4);self.assertEqual(len(calls),2)
  before=d.buffer.value;cursor=d.buffer.cursor;fail[0]=True;d.handle('insert','X');self.assertEqual(len(calls),3);self.assertEqual(d.syntax,[]);self.assertIn('sample failure',d.syntax_error);d.buffer.secret=True;self.assertIsNone(d.syntax_error);d.buffer.secret=False
  d.layout(40,4);self.assertEqual(len(calls),3);self.assertEqual(d.handle('undo').kind,'change');self.assertEqual(d.buffer.value,before);self.assertEqual(d.buffer.cursor,cursor);self.assertEqual(len(calls),4)
  fail[0]=False;d.set_syntax_analyzer(analyze);self.assertEqual(len(calls),5);self.assertIsNone(d.syntax_error)
  d.buffer.secret=True;d.layout(40,4);self.assertEqual(d.syntax,[])
  with self.assertRaises(ValueError):d.set_syntax_analyzer(analyze)
  self.assertEqual(len(calls),5);d.buffer.secret=False;d.layout(40,4);self.assertEqual(len(calls),6)
  d.set_syntax_analyzer(None);d.handle('insert','Z');d.layout(40,4);self.assertEqual(len(calls),6);self.assertEqual(d.syntax,[])
 def test_atomic_stale_utf8_and_unknown_roles(self):
  d=TextDocument.editor('한é界');d.set_syntax([DocumentSpan(0,3,'warning')]);old=d.syntax
  with self.assertRaises(ValueError):d.set_syntax_analyzer(SQLAnalyzer(),SyntaxRequest('unknown',''))
  self.assertEqual(d.syntax,old)
  stale=SyntaxAnalysis('wrong','sql','oracle',[])
  with self.assertRaises(ValueError):d.set_syntax_analysis(stale)
  self.assertEqual(d.syntax,old)
  # Codepoint boundaries alone are valid analysis, but applying must preserve graphemes.
  split=SyntaxAnalysis(d.buffer.value,'custom','',[SyntaxToken(3,4,'keyword')]);split.validate(d.buffer.value)
  with self.assertRaises(ValueError):d.set_syntax_analysis(split)
  self.assertEqual(d.syntax,old)
  for spans in [[SyntaxToken(1,3,'keyword')],[SyntaxToken(0,3,'keyword'),SyntaxToken(2,6,'comment')],[SyntaxToken(0,0,'number')]]:
   with self.assertRaises(ValueError):SyntaxAnalysis(d.buffer.value,'','',spans).validate(d.buffer.value)
  tokens=[SyntaxToken(0,3,'identifier')];a=SyntaxAnalysis(d.buffer.value,'custom','',tokens);d.set_syntax_analysis(a);tokens[0].role='keyword';self.assertEqual(d.syntax[0].role,'body');d.handle('insert','x');d.layout(40,4);self.assertEqual(d.syntax,[])
  self.assertEqual(syntax_role_style('macro'),'syntax.function');self.assertEqual(syntax_role_style('lifetime'),'syntax.parameter')
 def test_styles_copy_dim_and_actual_dark_eight_cues(self):
  names=['keyword','function','type','string','number','comment','parameter']
  for theme in ['dark','light','blackwhite']:
   for colors in ['8','16','256','truecolor']:
    p=Palette(theme,colors)
    for surface in ['editor','button.focus']:
     c=Canvas(12,4,p,surface)
     for x,name in enumerate(names):
      s=syntax_style(p,'syntax.'+name,surface);self.assertEqual(s.background,p.style(surface).background);self.assertFalse(s.dim);c.write_style(x,0,'X',s,width=1)
      if theme=='dark'and colors=='8':
       self.assertEqual(s.bold,name in ['keyword','number']);self.assertEqual(s.underline,name in ['keyword','type','parameter']);self.assertEqual(s.italic,name in ['string','comment']);self.assertTrue(int(s.foreground)<8)
     raw=Style('7',p.style(surface).background,italic=True);c.write_style(0,1,'I',raw,width=1);c.write_style(1,1,'N',Style('7',raw.background),width=1);c.blit(c,Rect(0,1,2,1),0,2);self.assertTrue(c.data[2][0].style.italic);self.assertFalse(c.data[2][1].style.italic)
     c.write_style(8,2,'I',raw,width=1);c.write_style(9,2,'N',Style('7',raw.background),width=1);Shadow(ShadowOptions('dim')).draw(c,Rect(7,0,5,3),lambda child:None);self.assertTrue(c.data[2][8].style.dim and c.data[2][8].style.italic);self.assertTrue(c.data[2][9].style.dim);self.assertFalse(c.data[2][9].style.italic);self.assertIn(';3',c.ansi())
 def test_markup_detaches_and_recursive_refresh_rejected(self):
  calls=[];analyzer=SQLAnalyzer()
  def analyze(text,request):calls.append(text);return analyzer.analyze_syntax(text,request)
  d=TextDocument.editor('SELECT 1');d.set_syntax_analyzer(analyze);d.set_markup('[info]literal[/]');d.handle('insert','x');self.assertEqual(len(calls),1)
  def recursive(text,request):
   if len(calls)>1:d.set_syntax_analyzer(None)
   calls.append(text);return analyzer.analyze_syntax(text,request)
  d=TextDocument.editor('SELECT 1');calls.clear();d.set_syntax_analyzer(recursive);d.handle('insert',' ');d.handle('insert','X');self.assertIsNotNone(d.syntax_error);self.assertEqual(d.syntax,[])
