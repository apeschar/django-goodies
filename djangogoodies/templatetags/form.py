import datetime

from django import template
import lxml
from lxml import etree

register = template.Library()

class FormNode(template.Node):
    find_fields = etree.XPath('//select[@name] | //input[@name]')
    find_submit = etree.XPath('//input[type="submit"]')

    def __init__(self, nodelist, form, kwargs):
        self.nodelist = nodelist
        self.form = form
        self.kwargs = kwargs

    def _parse_xml(self, xml):
        root = etree.XML(u"<span>" + unicode(xml) + u"</span>")
        if len(root) == 1:
            return root[0]
        else:
            return root

    def _add_class(self, elem, cls):
        if elem.get('class') is None or elem.get('class').strip() == '':
            elem.set('class', cls)
        else:
            elem.set('class', elem.get('class') + ' ' + cls)

    def render(self, context):
        self.form = self.form.resolve(context)
        for k, v in self.kwargs.items(): self.kwargs[k] = v.resolve(context)

        method = self.kwargs.get('method', '').upper()
        if method not in ('GET', 'POST'): method = 'POST'
        action = self.kwargs['action']
        error_class = self.kwargs.get('error_class')
        html = dict([(k[5:], v) for k, v in self.kwargs.items() if k[:5] == 'html.'])

        output = self.nodelist.render(context)
        form = etree.XML("<form>%s</form>" % output)
        form.set('method', method)
        form.set('action', action)
        form.set('enctype', 'multipart/form-data')
        for k, v in html.items(): form.set(k, v)

        fields = self.find_fields(form)
        for elem in fields:
            assert elem.tag in ('input', 'select'), 'invalid tag'
            name = elem.get('name')
            try:
                field = [f for f in self.form if f.name == name][0]
            except IndexError:
                continue
            field_elem = self._parse_xml(unicode(field))
            for name, value in elem.attrib.items():
                if name in ('name', 'value'): continue
                field_elem.attrib[name] = value
            field_elem.tail = elem.tail
            if error_class is not None and field.errors:
                self._add_class(field_elem, error_class)
            elem.getparent().replace(elem, field_elem)
        
        if len(self.find_submit(form)) == 0:
            div = etree.Element('div')
            div.set('style', 'display:none;')
            submit = etree.Element('input')
            submit.set('type', 'submit')
            div.append(submit)
            form.append(div)

        return unicode(etree.tostring(form))

@register.tag(name='form')
def do_form(parser, token):
    bits = token.split_contents()[1:]
    if len(bits) < 1:
        raise template.TemplateSyntaxError, "form tag expects at least one argument"
    form = parser.compile_filter(bits.pop(0))
    kwargs = {}
    for i in bits:
        try:
            a, b = [x.strip() for x in i.split('=', 1)]
        except ValueError:
            raise template.TemplateSyntaxError, \
                "argument syntax wrong: should be key=value"
        else:
            if a not in ('method', 'action', 'error_class') and a[:5] != 'html.':
                raise template.TemplateSyntaxError, "unknown argument: %s" % a
            kwargs[a] = parser.compile_filter(b)
    if not kwargs.has_key('action'):
        raise template.TemplateSyntaxError, "required argument: action"

    nodelist = parser.parse(('endform',))
    parser.delete_first_token()

    return FormNode(nodelist, form, kwargs)
