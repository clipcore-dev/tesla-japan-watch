import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from market import summarise
class MarketSafety(unittest.TestCase):
 def fixture(self,total=4):
  return f'''<table><tr><th colspan="2">中古車情報の相場</th><th>2023年</th><th>2024年</th></tr><tr><th colspan="2">合計{total}台</th><th>2台</th><th>2台</th></tr><tr><th>300万円以上</th><th><a href="/?PMIN=3000000&amp;PMAX=">2台</a></th><td>0</td><td>2</td></tr><tr><th>200万円〜</th><th><a href="/?PMIN=2000000&amp;PMAX=2999999">2台</a></th><td>2</td><td>0</td></tr></table>'''
 def test_median_bin_and_open_upper_bound(self):
  d=summarise(self.fixture());self.assertEqual(d['years'][0]['medianLowerManYen'],200);self.assertEqual(d['years'][0]['medianUpperManYen'],300);self.assertIsNone(d['years'][1]['medianUpperManYen']);self.assertTrue(d['years'][0]['smallSample'])
 def test_rejects_changed_totals(self):
  with self.assertRaises(ValueError):summarise(self.fixture(total=5))
 def test_rejects_unparseable_page(self):
  with self.assertRaises(ValueError):summarise('<h1>Site unavailable</h1>')
if __name__=='__main__':unittest.main()
