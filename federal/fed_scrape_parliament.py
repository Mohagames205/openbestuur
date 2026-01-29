from bs4 import BeautifulSoup
from urllib.request import Request, urlopen

req = Request("https://www.dekamer.be/kvvcr/showpage.cfm?section=/depute&language=nl&cfm=cvlist54.cfm?legis=56&today=y")
html_page = urlopen(req).read()

soup = BeautifulSoup(html_page, "html.parser")

print(soup.table)