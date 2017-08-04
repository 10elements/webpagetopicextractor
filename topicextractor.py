import nltk
import string
import itertools
from nltk.stem.snowball import SnowballStemmer
from contentcrawler import ContentCrawler
from collections import defaultdict
from collections import Iterable

class InvalidKeyError(Exception):
    pass

class TopicExtractor:
    def __init__(self, text, grammar = r'NP: {(<JJ>* <NN.*>+ <IN>)? <JJ>* <NN.*>+}',
                       stop_words = set(nltk.corpus.stopwords.words('english')), puncts = set(string.punctuation),
                       stemmer = SnowballStemmer('english')):
        """
        
        :param text: raw text of the target page
        :type text: dict, dict['title'] is a string, dict['content'] is a list of strings
        :raises TypeError: raises if text is not a dict instance
        :raises InvalidKeyError: raises if 'title' ot 'content' is not key
        """
        if not isinstance(text, dict):
            raise TypeError('text must be a dict object')
        if 'title' not in text or 'content' not in text:
            raise InvalidKeyError('text must have "title" and "content" keys')
        if not isinstance(grammar, str):
            raise TypeError('grammar must be a str instance')
        if not isinstance(stop_words, Iterable):
            raise TypeError('stop_words must be iterable')
        if not  isinstance(puncts, Iterable):
            raise TypeError('puncts must be iterable')
        self.__raw_text = text
        try:
            self.__chunk_parser = nltk.RegexpParser(grammar)
        except:
            raise
        self.__stop_words = stop_words
        self.__puncts = puncts
        self.__stemmer = stemmer

    @staticmethod
    def chunk(IBO_tag_list):
        """
        help function to chunk a list of IBO tags to a list of Noun Phrases
        
        :param IBO_tag_list: the IBO tag list to be chunked
        :type IBO_tag_list: iterable of 3-tuples (word, tag, IBO-tag)
        :return: a list of Noun phrases
        :rtype: list
        :raises TypeError: raises if input is not a list instance
        """
        if not isinstance(IBO_tag_list, list):
            raise TypeError('input must be a list')
        # group (word, tag, IBO-tag) based on the value of IBO-tag, tuples whose IBO-tag is 'O' is grouped together
        # while others retain their relative order
        sorted_IBO_tags_list = sorted(IBO_tag_list, key = lambda tag:tag[2] == 'O')
        result = []
        start = 0
        end = 1
        while end < len(sorted_IBO_tags_list):
            if sorted_IBO_tags_list[end][2].startswith('B'):
                result.append(' '.join((tag[0] for tag in sorted_IBO_tags_list[start : end])))
                start = end
            elif sorted_IBO_tags_list[end][2] == 'O':
                break
            end += 1
        result.append(' '.join((tag[0] for tag in sorted_IBO_tags_list[start : end])))
        return result

    def __process(self, text):
        """
        helper method to extract candidate phrases from text
                
        :param text: a list of strs
        :type text: list
        :return: a list of candidate phrases
        :rtype: list
        """
        # generator of strings, strip off the leading and trailing white spaces for each strings of text and
        # remove empty strings
        stripped = filter(lambda p: len(p) != 0 and p != 'None', (para.strip() for para in text))

        # generator of lists of tuples (word, POS-tag)
        tagged_sents = (nltk.pos_tag(nltk.word_tokenize(sent)) for para in stripped
                                for sent in nltk.sent_tokenize(para))

        # generator of chunk trees
        chunked_sents = (self.__chunk_parser.parse(sent) for sent in tagged_sents)

        # generator of lists of 3-tuples (word, tag, IBO-tag)
        IBO_tags = (nltk.chunk.tree2conlltags(tree) for tree in chunked_sents)

        # generator of Noun Phrases
        NP = itertools.chain(*(TopicExtractor.chunk(tag_list) for tag_list in IBO_tags))

        # generator of Noun Phrases, excluding stop words and punctuations
        filtered_NP = (NP.lower() for NP in NP if NP not in self.__stop_words
                               and not all(c in self.__puncts for c in NP) and len(NP) > 2)
        return filtered_NP

    def __extract_candidates(self):
        """
        extract candidate phrases based on the given grammar to match, stop words and punctuations to exclude
        
        :return: a list of candidate phrases
        :rtype: list
        """
        all_candidates = []
        title = self.__raw_text['title']
        title_candidates = self.__process(title)
        content = self.__raw_text['content']
        content_candidates = self.__process(content)
        all_candidates.extend(title_candidates)
        all_candidates.extend(content_candidates)
        return all_candidates

    def rank_candidates(self):
        """
        rank candidates phrases based on term frequencies
        
        :return: a list of tuples (phrase, frequency) sorted based on decreasing order of term frequencies
        :rtype: list
        """
        all_candidates = self.__extract_candidates()
        candidates_freq = defaultdict(int)
        for candidate in all_candidates:
            candidates_freq[candidate] += 1
        return sorted(candidates_freq.items(), key = lambda e:-e[1])

def main():
    crawler = ContentCrawler('https://stackoverflow.com/questions/4668621/how-to-check-if-an-object-is-iterable-in-python')
    page_content = crawler.crawl()
    extractor = TopicExtractor(page_content)
    ranks = extractor.rank_candidates()
    for r in ranks:
        print(r)

if __name__ == '__main__':
    main()