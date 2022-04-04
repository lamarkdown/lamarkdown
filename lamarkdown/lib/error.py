'''
The Error class represents errors occurring during compilation. These are incorporated into the
HTML document (for visibility) and/or output to the console.
'''
#from markdown.util import AtomicString
#import html
#import traceback
#from xml.etree import ElementTree

#RESET = '\033[0m'

#class Message:
    #def __init__(self, location: str, msg: str, *details_list: str):
        #self._location = location
        #self._msg = msg
        #self._details_list = details_list
        
    #def print(self):
        #print(f'{self.LABEL_COLOUR}{self.TAG}{self._location}{RESET} {self.MSG_COLOUR}{self._msg}{RESET}')
        #for details in self._details_list:
            #print('--')
            #print(details.strip())
        #if self._details_list:
            #print('--')
                
#class ProgressMessage(Message):
    #LABEL_COLOUR = '\033[35;1m'
    #MSG_COLOUR = '\033[37;1m'
    #TAG = ''
    
#class WarningMessage(Message):
    #LABEL_COLOUR = '\033[33;1m'
    #MSG_COLOUR = '\033[37;1m'
    #TAG = '[!] '
    
#class ErrorMessage(Message):
    #LABEL_COLOUR = '\033[31;1m'
    #MSG_COLOUR = '\033[37;1m'
    #TAG = '[!!]'    
    
    #PANEL_STYLE = 'border: 2px dashed yellow; background: #800000; padding: 1ex;'
    #MSG_STYLE = 'font-weight: bold; color: white;'
    #LOCATION_STYLE = 'color: yellow;'
    #DETAILS_STYLE = ''
    
    #MAX_ROWS = 30
    #MAX_COLS = 110
        
    #@staticmethod
    #def from_exception(location: str, e: Exception, *details_list: str) -> 'Error':
        #return Error(location, str(e), ''.join(traceback.format_exc()), *details_list)


    #def as_dom_error(self) -> ElementTree.Element:
        #panel_elem = ElementTree.Element('form', style = self.PANEL_STYLE)
        #msg_elem = ElementTree.SubElement(panel_elem, 'div', style = self.MSG_STYLE)
        #location_elem = ElementTree.SubElement(msg_elem, 'span', style = self.LOCATION_STYLE)

        #location_elem.text = AtomicString(f'[{self._location}]')
        #location_elem.tail = AtomicString(f' {self._msg}')

        #if self._details_list:
            #cols = str(max(10, min(self.MAX_COLS,
                #max(len(line) for details in self._details_list for line in details.splitlines())
            #)))

            #for details in self._details_list:
                #details_elem = ElementTree.SubElement(panel_elem,
                    #'textarea',
                    #style = self.DETAILS_STYLE,
                    #rows = str(max(1, min(self.MAX_ROWS, details.count('\n') + 1))),
                    #cols = cols,
                    #readonly = ''
                #)
                #details_elem.text = AtomicString(details)

        #return panel_elem


    #def as_html_error(self) -> str:
        #return ElementTree.tostring(self.to_element(), encoding = 'unicode')


