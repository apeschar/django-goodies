import datetime

from django import template
import lxml
from lxml import etree

register = template.Library()

class FormNode(template.Node):
    parser = etree.XMLParser()
    find_fields = etree.XPath('//select[@name] | //input[@name] | //textarea[@name]')
    find_submit = etree.XPath('//input[@type="submit"]')
    find_file_inputs = etree.XPath('//input[@type="file"]')
    find_elements_to_fill = etree.XPath('//textarea | //select')

    def __init__(self, nodelist, form, kwargs, flags):
        self.nodelist = nodelist
        self.form = form
        self.kwargs = kwargs
        self.flags = flags

    def _parse_xml(self, xml):
        root = etree.XML(u"<span>" + unicode(xml) + u"</span>", self.parser)
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
        action = self.kwargs.get('action', '')
        error_class = self.kwargs.get('error_class')
        html = dict([(k[5:], v) for k, v in self.kwargs.items() if k[:5] == 'html.'])
        strict = 'strict' in self.flags
        messages = 'messages' in self.flags

        output = self.nodelist.render(context)
        form = etree.XML("<form>%s</form>" % output, self.parser)
        form.set('method', method)
        form.set('action', action)

        for k, v in html.items(): form.set(k, v)

        fields = self.find_fields(form)
        fields_used = []
        for elem in fields:
            name = elem.get('name')
            try:
                field = [f for f in self.form if f.name == name][0]
            except IndexError:
                if strict:
                    raise Exception('Unknown field: %s' % name)
                else:
                    continue
            if strict and name in fields_used:
                raise Exception('Field used twice: %s' % name)
            fields_used.append(name)
            field_elem = self._parse_xml(unicode(field))
            for name, value in elem.attrib.items():
                if name in ('name', 'value'): continue
                field_elem.attrib[name] = value
            field_elem.tail = elem.tail
            if error_class is not None and field.errors:
                self._add_class(field_elem, error_class)
            
            # Replace element by new element.
            parent = elem.getparent()
            index = -1
            for el in parent:
                index += 1
                if el == elem: break
            parent[index] = field_elem

            # Insert error messages.
            if messages and field.errors:
                errors_elem = etree.Element('ul')
                errors_elem.set('class', 'errors')
                for error in field.errors:
                    node = etree.Element('li')
                    node.text = unicode(error)
                    errors_elem.append(node)
                parent.insert(index + 1, errors_elem)
        if strict:
            for field in self.form:
                if field.name not in fields_used:
                    raise Exception('Field not used: %s' % field.name)
        
        if len(self.find_submit(form)) == 0:
            div = etree.Element('div')
            div.set('style', 'display:none;')
            submit = etree.Element('input')
            submit.set('type', 'submit')
            div.append(submit)
            form.append(div)
        
        if len(self.find_file_inputs(form)) > 0:
            form.set('enctype', 'multipart/form-data')
        form.set('enctype', 'multipart/form-data')

        for node in self.find_elements_to_fill(form):
            if len(node) == 0 and node.text is None:
                node.text = ''

        return unicode(etree.tostring(form))

@register.tag(name='form')
def do_form(parser, token):
    bits = token.split_contents()[1:]
    if len(bits) < 1:
        raise template.TemplateSyntaxError, "form tag expects at least one argument"
    form = parser.compile_filter(bits.pop(0))
    kwargs = {}
    flags = []
    for i in bits:
        if i in ('strict', 'messages'):
            flags.append(i)
        else:
            try:
                a, b = [x.strip() for x in i.split('=', 1)]
            except ValueError:
                raise template.TemplateSyntaxError, \
                    "argument syntax wrong: should be key=value"
            else:
                if a not in ('method', 'action', 'error_class') and a[:5] != 'html.':
                    raise template.TemplateSyntaxError, "unknown argument: %s" % a
                kwargs[a] = parser.compile_filter(b)

    nodelist = parser.parse(('endform',))
    parser.delete_first_token()

    return FormNode(nodelist, form, kwargs, flags)
