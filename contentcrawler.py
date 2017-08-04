import requests
from bs4 import BeautifulSoup
from bs4.element import Comment

class ContentCrawler:
    """
    Crawler to crawl all the visible text data from a given page, without stripping the white spaces and 
    removing the stop words.
    
    """
    def __init__(self, target_url):
        """
        Create an ContentCrawler instance from target_url        
        
        :param target_url: url of the page to scrape from
        :type target_url: str
        """
        self.__target_url = target_url

    @staticmethod
    def filter_invalid_str(s):
        """
        Filter out comment strings and strings whose parents tags are <style> and <script>
        
        :param s: the 
        :type s: NavigableString
        :return: True if s is not a comment and s's parent is neither <style> nor <script>
        :rtype: Boolean
        """
        return s.parent.name not in ['style', 'script'] and not isinstance(s, Comment)

    def crawl(self, links_only = True):

        """
        Crawl text from the target page. If links_only if True, then it only crawls text of links, else it crawls all 
        visible text of the target page.
         
        :param links_only: True if only links' text is wanted, False if all visible text is wanted
        :type links_only: bool
        :return:  A dictionary where dict['title'] is a list instance containing the title of the page 
        and dict['content'] is a list instance containing links' text or all visible text.
        :rtype: dict
        :raises requests.Timeout: raise if request time out
        :raises requests.HTTPError: raise if status code is unsuccessful
        :raises requests.URLRequired: if url is invalid
        """
        response = requests.get(self.__target_url, timeout = 3)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        page_result = {}
        page_result['title'] = [str(soup.title.string)]
        if links_only:
            page_content = list(filter(lambda s: s != '' and s != 'None',
                                       (str(link.string).strip() for link in soup.body.find_all('a'))))
        else:
            page_content = list(map(str, soup.body.find_all(string=ContentCrawler.filter_invalid_str)))
        page_result['content'] = page_content
        return page_result