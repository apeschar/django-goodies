import datetime

from django import template
import lxml
from lxml import etree

register = template.Library()

class MenuNode(template.Node):
    find_links = etree.XPath('//a[@link]')
    
    def __init__(self, nodelist, kwargs):
        self.nodelist = nodelist
        self.kwargs = kwargs

    def render(self, context):
        output = self.nodelist.render(context)
        root = etree.XML("<root>%s</root>" % output)

        for k, v in self.kwargs.items(): self.kwargs[k] = v.resolve(context)
        link_class = self.kwargs.get('link_class')
        active = self.kwargs.get('active')
        active_class = self.kwargs.get('active_class')
        active_id = self.kwargs.get('active_id')
        
        links = self.find_links(root)
        for link in links:
            link_id = link.get('link')
            del link.attrib['link']
            
            add_class = []
            set_id = None

            if link_class:
                add_class.append(link_class)
            if active and link_id == active:
                if active_class:
                    add_class.append(active_class)
                if active_id:
                    set_id = active_id
            if add_class:
                attr_class = ' '.join(add_class)
                if link.get('class'):
                    link.set('class', (link.get('class') + ' ' + attr_class).lstrip())
                else:
                    link.set('class', attr_class)
            if set_id:
                link.set('id', set_id)
        
        return unicode(etree.tostring(root)[6:-7])

@register.tag(name='menu')
def do_menu(parser, token):
    bits = token.split_contents()[1:]
    kwargs = {}
    for i in bits:
        try:
            a, b = [x.strip() for x in i.split('=', 1)]
            if a not in ('active', 'active_class', 'active_id', 'link_class'):
                raise template.TemplateSyntaxError, "Unknown argument: %s" % a
            kwargs[a] = parser.compile_filter(b)
        except ValueError:
            raise template.TemplateSyntaxError, \
                "Argument syntax wrong: should be key=value"

    nodelist = parser.parse(('endmenu',))
    parser.delete_first_token()

    return MenuNode(nodelist, kwargs)
