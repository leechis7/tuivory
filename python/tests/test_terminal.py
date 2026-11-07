import json,os,unittest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import Mock,patch
from tuivory import InputDecoder,Terminal
F=json.loads((Path(__file__).resolve().parents[2]/'design/terminal-input-cases.json').read_text())

class TerminalInput(unittest.TestCase):
    def test_shared_incremental_cases(self):
        for case in F['cases']:
            with self.subTest(case=case['name']):
                decoder=InputDecoder();events=[]
                for chunk in case['chunks']:
                    decoder.feed(bytes.fromhex(chunk))
                    while (event:=decoder.next())is not None:events.append(asdict(event))
                if case.get('flush_escape'):
                    while (event:=decoder.next(True))is not None:events.append(asdict(event))
                self.assertEqual(events,case['events'])

    def test_invalid_utf8_mouse_and_paste_limit(self):
        d=InputDecoder();d.feed(b'\xff');self.assertEqual(d.next().text,'\ufffd')
        d.feed(b'\x1b[<0;0;2M');self.assertEqual(d.next().key,'unknown')
        d.feed(b'\x1b[<1000000001;1;1M');self.assertEqual(d.next().key,'unknown')
        d.feed(b'\x1b[200~'+b'a'*(16*1024*1024+1)+b'\x1b[201~')
        self.assertEqual(d.next().key,'paste_rejected')
        self.assertIsNone(d.next())

    def test_closed_and_invalid_read_timeout(self):
        terminal=Terminal()
        self.assertEqual(terminal.read(0).key,'eof')
        for timeout in [-1,float('nan'),float('inf'),3601]:
            with self.assertRaises(ValueError):terminal.read(timeout)

    @unittest.skipUnless(os.name=='posix','POSIX lifecycle')
    def test_open_failure_restores_both_modes_and_attributes(self):
        import termios
        terminal=Terminal(mouse_motion=True);saved=[1,2,3]
        stdin=Mock();stdin.isatty.return_value=True;stdin.fileno.return_value=0
        stdout=Mock();stdout.isatty.return_value=True
        with patch('sys.stdin',stdin),patch('sys.stdout',stdout),patch('termios.tcgetattr',return_value=saved),patch('tty.setraw'),patch('termios.tcsetattr')as restore:
            failure=OSError('write failed')
            with patch.object(terminal,'write',side_effect=[failure,None])as write:
                with self.assertRaisesRegex(OSError,'write failed'):terminal.__enter__()
                self.assertIn('\x1b[?1002l',write.call_args_list[1].args[0])
            restore.assert_called_once_with(0,termios.TCSADRAIN,saved)
            self.assertIsNone(terminal._saved)

    def test_double_open_preserves_saved_state(self):
        terminal=Terminal();terminal._saved=['original']
        with self.assertRaisesRegex(RuntimeError,'already active'):terminal.__enter__()
        self.assertEqual(terminal._saved,['original'])
