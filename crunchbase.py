import datetime
import urllib
import urllib2
import json

ENTITY_MAP = [
    ('company', 'companies'),
    ('person', 'people'),
    ('financial-organization', 'financial-organizations'),
    ('product', 'products')
]


class CrunchBase(object):
    """
    Access the CrunchBase API.
    """
    def __init__(self, api_key):
        self.api_str = "api_key=%s" % api_key

    def open(self, filename, qualifiers=None, base="api", version=1):
        """
        Open a url and return the page as dict or list via JSON.
        """
        qual_string = '' if not qualifiers else '&' + urllib.urlencode(qualifiers)
        url = 'http://%s.crunchbase.com/v/%s/%s?%s%s' % (base, version, filename, self.api_str, qual_string)
        print url
        resource = urllib2.urlopen(url)
        try:
            return json.loads(resource.read())
        except ValueError:
            return None

    def companies(self):
        self.open('companies')

    def search(self, query, entity=None, field=None, namespace=None, requirements=[]):
        qualifiers = dict(query=query)
        if entity: qualifiers['entity'] = entity
        if field: qualifiers['field'] = field
        if namespace: qualifiers['namespace'] = namespace
        return CrunchList(self, 'search.js', qualifiers)

    def get_permalink(self, namespace, name=None, first_name=None, last_name=None):
        if namespace == 'people':
            qualifiers = dict(first_name=first_name, last_name=last_name)
        else:
            qualifiers = dict(name=name)
        filename = "%s/permalink/" % namespace
        try:
            entity = self.open(filename, qualifiers)
        except urllib2.HTTPError:
            return None
        return entity

    def entity(self, namespace, permalink=None, name=None, first_name=None, last_name=None):
        ns_plural = dict(ENTITY_MAP)[namespace]
        if permalink:
            pass
        elif name or first_name or last_name:
            pl = self.get_permalink(ns_plural, name, first_name, last_name)
            if pl:
                permalink = pl['permalink']
            else:
                raise Exception('No such %s' % namespace)
        else:
            raise Exception('Neither permalink nor name provided')
        return self.open('%s/%s.js' % (namespace, permalink))

    def fin_org(self, permalink=None, name=None):
        return FinancialOrg(self.entity('financial-organization', permalink=permalink, name=name))

    def company(self, permalink=None, name=None):
        return Company(self.entity('company', permalink=permalink, name=name))

    def product(self, permalink=None, name=None):
        return Product(self.entity('product', permalink=permalink, name=name))

    def person(self, permalink=None, first_name=None, last_name=None):
        return Person(self.entity('person', permalink=permalink, first_name=first_name, last_name=last_name))

    def get_full_object(self, crunch_entity):
        """
        Call the api and return all details.
        """
        ret = self.entity(namespace=crunch_entity.namespace, permalink=crunch_entity.permalink)
        print "%s" % ret
        return crunch_entity.__class__(ret)



class CrunchList(object):
    cb = None
    length = None
    cache = None
    current_page = None
    current_item = None
    filename = ""
    qualifiers = {}
    requirements = ['milestones', 'investments']

    def __init__(self, cb, filename, qualifiers):
        self.cb = cb
        self.filename = filename
        self.qualifiers = qualifiers
        self.cache = cb.open(filename, qualifiers)
        self.page = self.cache['page']
        self.length = self.cache['total']
        self.current_item = 0

    def __iter__(self):
        return self

    def next(self):
        if self.length == self.current_item:
            raise StopIteration
        if self.cache:
            ret = self.cache['results'][self.current_item % 10]
        else:
            ret = None
        if self.current_item % 10 == 9 and self.page * 10 != self.length:
            self.page += 1
            qualifiers = {}
            qualifiers.update(self.qualifiers)
            qualifiers.update({'page': self.page})
            self.cache = self.cb.open(self.filename, qualifiers)
        self.current_item += 1
        if ret:
            return dispatch_to_object(ret)
        else:
            return None

    def __str__(self):
        return "%s.js&%s" % (self.filename, urllib.urlencode(self.qualifiers))


def dispatch_to_object(entity_dict):
    namespace = entity_dict['namespace']
    if namespace == 'company':
        return Company(entity_dict)
    elif namespace == 'product':
        return Product(entity_dict)
    elif namespace == 'financial-organization':
        return FinancialOrg(entity_dict)
    elif namespace == 'person':
        return Person(entity_dict)


class CrunchEntity(object):
    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.full_name)

    @property
    def full_name(self):
        try:
            return self.name
        except AttributeError:
            try:
                return "%s %s" % (self.first_name, self.last_name)
            except AttributeError:
                return "No name"


class Product(CrunchEntity):
    namespace = 'product'
    name = ""
    permalink = ""
    crunchbase_url = None
    overview = ""
    image = None
    homepage_url = None

    def __init__(self, prod_dict):
        for k, v in prod_dict.items():
            setattr(self, k, v)


class Company(CrunchEntity):
    namespace = 'company'
    category_code = ""
    name = ""
    permalink = ""
    crunchbase_url = None
    overview = ""
    image = None
    homepage_url = None
    description = ""
    updated_at = None
    offices = None
    funding_rounds = None
    total_money_raised = 0
    founded_date = None
    deadpooled_date = None

    def __init__(self, prod_dict):
        dp_dict = {}
        f_dict = {}
        for k, v in prod_dict.items():
            if k.startswith('deadpooled_') and k != "deadpooled_url":
                dp_dict[k.split('deadpooled_')[1]] = v
            elif k.startswith('founded_'):
                f_dict[k.split('founded_')[1]] = v
            elif k == 'funding_rounds':
                self.funding_rounds = []
                for round in v:
                    print "new round"
                    self.funding_rounds.append(FundingRound(round))
            else:
                setattr(self, k, v)
        try:
            self.deadpooled_date = datetime.date(**dp_dict)
        except:
            pass
        try:
            self.founded_date = datetime.date(**f_dict)
        except:
            pass


class FundingRound(object):
    raised_amount = 0
    raised_currency_code = 'USD'
    investments = None
    source_description = ""
    funded_date = None
    round_code = None
    source_url = None
    crunchbase_id = None

    def __init__(self, fr_dict):
        funded_dict = {}
        for k, v in fr_dict.items():
            if k.startswith('funded_'):
                funded_dict[k.split('funded_')[1]] = v
            elif k == 'investments':
                print 'a'
                self.investments = []
                for investment in v:
                    print 'b'
                    self.investments.extend(investor(investment))
                    print "inv length %s" % len(self.investments)
            else:
                setattr(self, k, v)
        try:
            if not funded_dict['day']: funded_dict['day'] = 1
            if not funded_dict['month']: funded_dict['month'] = 7
            self.funded_date = datetime.date(**funded_dict)
        except:
            pass
        print self

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.desc())

    def desc(self):
        series = "[unattributed]" if not self.round_code else self.round_code
        return "$%s (%s) Series %s: funded %s by %s" % (
            self.raised_amount, self.raised_currency_code, series, self.funded_date, self.investments
        )


def investor(investment):
    ext = []
    p, c, f = investment['person'], investment['company'], investment['financial_org']
    if p:
        ext.append(Person(p))
    if c:
        ext.append(Company(c))
    if f:
        ext.append(FinancialOrg(f))
    print 'len %s' % len(ext)
    return ext


class Person(CrunchEntity):
    namespace = 'person'
    first_name = ""
    last_name = ""
    permalink = ""
    crunchbase_url = None
    created_at = None
    overview = ""
    image = {}
    homepage_url = None
    updated_at = None
    affiliation_name = ""
    web_presences = []
    investments = None
    blog_url = ""
    twitter_username = ""

    def __init__(self, fr_dict):
        for k, v in fr_dict.items():
            if k == 'investments':
                self.investments = []
                for investment in v:
                    self.investments.append(FundingRound(investment['funding_round']))
            else:
                setattr(self, k, v)


class FinancialOrg(CrunchEntity):
    namespace = 'financial-organization'
    name = ""
    permalink = ""
    crunchbase_url = None
    alias_list = None
    created_at = None
    overview = ""
    image = {}
    homepage_url = None
    description = ""
    updated_at = None
    offices = None
    investments = None
    milestones = None
    founded_date = None

    def __init__(self, prod_dict):
        f_dict = {}
        for k, v in prod_dict.items():
            if k.startswith('founded_'):
                f_dict[k.split('founded_')[1]] = v
            elif k == 'investments':
                self.investments = []
                for investment in v:
                    self.investments.append(FundingRound(investment['funding_round']))
            else:
                setattr(self, k, v)
        try:
            self.founded_date = datetime.date(**f_dict)
        except:
            pass

