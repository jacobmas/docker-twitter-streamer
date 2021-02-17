# fourFn.py
#
# parsing of Twitter-style search queries
#
from pyparsing import (
    Literal,
    Word,
    Group,
    Forward,
    alphas,
    alphanums,
    Combine,
    Keyword,
    Regex, Optional,
    OneOrMore,
    ParseException,
    CaselessKeyword,
    Suppress,
    delimitedList,
    quotedString,
    QuotedString
)
from functools import reduce
import math
import operator
import re
import logging

my_logger = logging.getLogger(__name__)
log_val = logging.ERROR - int(0) * 10
log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
log_level = max(log_val, logging.DEBUG)
logging.basicConfig(format=log_fmt, level=log_level)

class TwitterSeachQuery:
    def __init__(self,query_str,keyword_funcs):
        """Create a Twitter-style (used in many other systems as well) search query
         :param query_str: the query format string
         :param keyword_funcs: a list of single-input functions named, ideally
         so one can do things like from:user in the search
         """
        self.exprStack = []
        self.query_str=query_str
        self.bnf = None
        self.keyword_funcs=keyword_funcs
        self.parsed_str=None
        self.parseString()



    def tokenize_text(self,input_str):
        """tokenize the text being searched using non-word characters, hopefully non-word is extensive enough
         to include - and such if not quoted strings will work for that
        :param input_str: string to tokenize

          """
        return re.split(r'\W+',input_str)

    def check_word(self,keyword,tokenized_text):
        #TODO fix text should be tokenized first
        return reduce(lambda x,y:x or y,
                      map(lambda s:re.fullmatch(keyword,s,flags=re.I) is not None,tokenized_text))

    def check_keyword(self,keyword,keyword_val):
        #TODO: fix
        return True


    def push_first(self,loc,toks):
        my_logger.warning(f"loc={loc},toks={toks}")
        if len(toks)>0:
            self.exprStack.append(toks[0])

    def push_and(self,loc,toks):
        my_logger.warning(f"pushing and, loc={loc},toks={toks}")
        if len(toks)>0:
            self.exprStack.append("AND")


    def push_unary_minus(self,toks):
        for t in toks:
            if t == "-":
                self.exprStack.append("unary -")
            else:
                break

    def is_type(self,text):
        pass
        # TODO is:SOMETHING this will need to be source dependent figure it out later

    def parseString(self):
        """
        Parse string.
        Initial attempt at grammar, needs restructuring.

        ANDop  :: 'AND'
        ORop   :: 'OR'
        lpar :: '('
        rpar :: ')'
        keyword :: alphas
        result :: alphanums
        word :: alphanums
        hashtag :: COMBINE('#' word)
        cashtag :: COMBINE ('$' word)
        atom    :: COMBINE('-' atom) | word | COMBINE(keyword ':' result) | lpar expr rpar | hashtag | cashtag
        term    :: atom [ ORop atom ]*
        expr    :: term [ ANDop term ]*
        """
        if self.bnf is None:
            ANDop = Keyword('AND')
            ORop = Keyword('OR')
            colon=Literal(':')
            word = ~colon + ~ORop+ ~ANDop + Word(alphanums,min=1)
            keyword = ~colon + ~ORop + ~ANDop + Word(alphas,min=1)
            quoted = quotedString
            hashtag = Combine(Literal('#')+Word(alphanums))
            cashtag = Combine(Literal('$')+Word(alphanums))
            minus = Literal('-')
            lpar, rpar = map(Suppress, "()")
            expr = Forward()

            atom = Forward()
            atom <<= (minus[...].setParseAction(self.push_first)+
                      (Group(lpar + expr + rpar)
                |
                Group(keyword.setResultsName("keyword") + colon + word.setResultsName("value")).setParseAction(self.push_first)
                       | hashtag.setParseAction(self.push_first)
                       | cashtag.setParseAction(self.push_first)
                       | Group(quoted.setResultsName('quote')).setParseAction(self.push_first)
                |
                word.setParseAction(self.push_first).setResultsName('word')[1]
            )
            ).setParseAction(self.push_unary_minus)

            # AND is optional word1 word2 implicitly is word1 AND word2
            term = Forward()
            term <<= atom + (ORop + atom).setParseAction(self.push_first)[...]
            expr <<= term + (Optional(ANDop) + term).setParseAction(self.push_and)[...]
            self.bnf = expr
            self.parsed_str=self.bnf.parseString(self.query_str, parseAll=True)


    def evaluate_search(self,input_str,data=None):
        """ Helper function that tokenizes the input string and then calls evaluate stack
        :param input_str: the input string to search on
        :param data: metadata associated with the string, used for evaluation of
        keyword functions like from:username since:time and the like, does not need to have a
        specified format but must be compatible with the keyword functions given
        """
        return self._evaluate_stack(input_str,self.tokenize_text(input_str),data)

    def _evaluate_stack(self,input_str,tok_input_str,data):

        op, num_args = self.exprStack.pop(), 0
        my_logger.warning(f"op={op},type={type(op)}")
        if op == "OR":
            op2=self._evaluate_stack(input_str,tok_input_str,data)
            op1=self._evaluate_stack(input_str,tok_input_str,data)
            return op1 or op2
        if op == "AND":
            op2=self._evaluate_stack(input_str,tok_input_str,data)
            op1=self._evaluate_stack(input_str,tok_input_str,data)
            return op1 and op2
        if 'quote' in op:
            my_logger.warning(f"quote={op}")
            return re.search(re.sub(r'[\'\"]+','',op['quote']),input_str,flags=re.I) is not None
        if 'keyword' in op and 'value' in op:
            my_logger.warning(f"keyword, op={op}")
            return self.check_keyword(op['keyword'],op['value'])
        elif op == 'unary -':
            next_op=self._evaluate_stack(input_str,tok_input_str,data)
            return not next_op
        elif isinstance(op,str):
            my_logger.warning(f"str={op}")
            return self.check_word(op,tok_input_str)
        else:
            my_logger.error(f"not list,op={op},type(op)={type(op)}")
            raise Exception("Should never get here should always have an op")
        return self._evaluate_stack(tok_input_str,data)


if __name__ == "__main__":

    def test(query_str,input,expected_val):

        query=TwitterSeachQuery(query_str)
        my_logger=(query.exprStack)
        val = query.evaluate_search(input)
        print(f"query={query_str},input={input}, success={val==expected_val}")


    #test("from:twitterdev OR is:reply", "fuck")
    test("'bob fred'", "ipad bob fred",True) # true
    test("'bob fred'", "ipad bob and fred",False) # false
    test("bob fred", "ipad bob and fred",True) #true
    test("bob fred", "ipad BoB and fred",True) #true
    test("bob", "bobB",False) #false
    test("bob fred", "bob", False)
    test("bob OR fred","bob",True)
    test("bob OR fred","fred",True)
    test("(bob) OR fred","fred",True)

    my_logger.setLevel(logging.DEBUG)
    test("-bob fred","fred",True)
    test("-bob fred","bob fred",False)
    test("-bob fred","bob",False)
    test("#bob", "fred", True)
    test("@bob", "fred", True)





"""
Test output:
>python fourFn.py
9 = 9 ['9'] => ['9']
-9 = -9 ['-', '9'] => ['9', 'unary -']
--9 = 9 ['-', '-', '9'] => ['9', 'unary -', 'unary -']
-E = -2.718281828459045 ['-', 'E'] => ['E', 'unary -']
9 + 3 + 6 = 18 ['9', '+', '3', '+', '6'] => ['9', '3', '+', '6', '+']
9 + 3 / 11 = 9.272727272727273 ['9', '+', '3', '/', '11'] => ['9', '3', '11', '/', '+']
(9 + 3) = 12 [['9', '+', '3']] => ['9', '3', '+']
(9+3) / 11 = 1.0909090909090908 [['9', '+', '3'], '/', '11'] => ['9', '3', '+', '11', '/']
9 - 12 - 6 = -9 ['9', '-', '12', '-', '6'] => ['9', '12', '-', '6', '-']
9 - (12 - 6) = 3 ['9', '-', ['12', '-', '6']] => ['9', '12', '6', '-', '-']
2*3.14159 = 6.28318 ['2', '*', '3.14159'] => ['2', '3.14159', '*']
3.1415926535*3.1415926535 / 10 = 0.9869604400525172 ['3.1415926535', '*', '3.1415926535', '/', '10'] => ['3.1415926535', '3.1415926535', '*', '10', '/']
PI * PI / 10 = 0.9869604401089358 ['PI', '*', 'PI', '/', '10'] => ['PI', 'PI', '*', '10', '/']
PI*PI/10 = 0.9869604401089358 ['PI', '*', 'PI', '/', '10'] => ['PI', 'PI', '*', '10', '/']
PI^2 = 9.869604401089358 ['PI', '^', '2'] => ['PI', '2', '^']
round(PI^2) = 10 [('round', 1), [['PI', '^', '2']]] => ['PI', '2', '^', ('round', 1)]
6.02E23 * 8.048 = 4.844896e+24 ['6.02E23', '*', '8.048'] => ['6.02E23', '8.048', '*']
e / 3 = 0.9060939428196817 ['E', '/', '3'] => ['E', '3', '/']
sin(PI/2) = 1.0 [('sin', 1), [['PI', '/', '2']]] => ['PI', '2', '/', ('sin', 1)]
10+sin(PI/4)^2 = 10.5 ['10', '+', ('sin', 1), [['PI', '/', '4']], '^', '2'] => ['10', 'PI', '4', '/', ('sin', 1), '2', '^', '+']
trunc(E) = 2 [('trunc', 1), [['E']]] => ['E', ('trunc', 1)]
trunc(-E) = -2 [('trunc', 1), [['-', 'E']]] => ['E', 'unary -', ('trunc', 1)]
round(E) = 3 [('round', 1), [['E']]] => ['E', ('round', 1)]
round(-E) = -3 [('round', 1), [['-', 'E']]] => ['E', 'unary -', ('round', 1)]
E^PI = 23.140692632779263 ['E', '^', 'PI'] => ['E', 'PI', '^']
exp(0) = 1.0 [('exp', 1), [['0']]] => ['0', ('exp', 1)]
exp(1) = 2.718281828459045 [('exp', 1), [['1']]] => ['1', ('exp', 1)]
2^3^2 = 512 ['2', '^', '3', '^', '2'] => ['2', '3', '2', '^', '^']
(2^3)^2 = 64 [['2', '^', '3'], '^', '2'] => ['2', '3', '^', '2', '^']
2^3+2 = 10 ['2', '^', '3', '+', '2'] => ['2', '3', '^', '2', '+']
2^3+5 = 13 ['2', '^', '3', '+', '5'] => ['2', '3', '^', '5', '+']
2^9 = 512 ['2', '^', '9'] => ['2', '9', '^']
sgn(-2) = -1 [('sgn', 1), [['-', '2']]] => ['2', 'unary -', ('sgn', 1)]
sgn(0) = 0 [('sgn', 1), [['0']]] => ['0', ('sgn', 1)]
sgn(0.1) = 1 [('sgn', 1), [['0.1']]] => ['0.1', ('sgn', 1)]
foo(0.1) failed eval: invalid identifier 'foo' ['0.1', ('foo', 1)]
round(E, 3) = 2.718 [('round', 2), [['E'], ['3']]] => ['E', '3', ('round', 2)]
round(PI^2, 3) = 9.87 [('round', 2), [['PI', '^', '2'], ['3']]] => ['PI', '2', '^', '3', ('round', 2)]
sgn(cos(PI/4)) = 1 [('sgn', 1), [[('cos', 1), [['PI', '/', '4']]]]] => ['PI', '4', '/', ('cos', 1), ('sgn', 1)]
sgn(cos(PI/2)) = 0 [('sgn', 1), [[('cos', 1), [['PI', '/', '2']]]]] => ['PI', '2', '/', ('cos', 1), ('sgn', 1)]
sgn(cos(PI*3/4)) = -1 [('sgn', 1), [[('cos', 1), [['PI', '*', '3', '/', '4']]]]] => ['PI', '3', '*', '4', '/', ('cos', 1), ('sgn', 1)]
+(sgn(cos(PI/4))) = 1 ['+', [('sgn', 1), [[('cos', 1), [['PI', '/', '4']]]]]] => ['PI', '4', '/', ('cos', 1), ('sgn', 1)]
-(sgn(cos(PI/4))) = -1 ['-', [('sgn', 1), [[('cos', 1), [['PI', '/', '4']]]]]] => ['PI', '4', '/', ('cos', 1), ('sgn', 1), 'unary -']
"""