import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('collect',Path(__file__).resolve().parents[1]/'scripts/collect.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
class Safeguards(unittest.TestCase):
 def test_rss_does_not_allow_script_url(self):
  x=c.items_from_rss('<rss><channel><item><title>unsafe</title><link>javascript:alert(1)</link></item><item><title>Valid</title><link>https://example.org/news</link></item></channel></rss>')
  self.assertEqual(len(x),1);self.assertEqual(x[0]['title'],'Valid')
 def test_stock_is_not_inferred_from_button(self):self.assertEqual(c.offers('<button>Add to cart</button>'),[])
 def test_explicit_stock_and_price(self):
  x=c.offers('<script type="application/ld+json">{"@type":"Product","offers":{"@type":"Offer","availability":"https://schema.org/OutOfStock","price":9900,"priceCurrency":"JPY"}}</script>')
  self.assertEqual(x[0]['availability'],'OutOfStock');self.assertEqual(x[0]['currency'],'JPY')
 def test_missing_station_list_is_not_mass_closure(self):
  with self.assertRaises(ValueError):c.stations('<html>Access denied</html>')
 def test_station_first_run_requires_real_detail_links(self):
  raw=''.join('<a href="/ja_jp/findus/location/supercharger/site'+str(i)+'">Station '+str(i)+'</a>' for i in range(25))
  self.assertEqual(len(c.stations(raw)),25)
 def test_scripts_are_removed_from_plain_text(self):self.assertEqual(c.plain('<p>Hello</p><script>evil()</script>'),'Hello')
if __name__=='__main__':unittest.main()
