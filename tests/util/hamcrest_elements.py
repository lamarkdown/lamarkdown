from hamcrest import *

def space():
    return described_as("␣", any_of(none(), matches_regexp(r'\s*')))

def is_element(tag, attrib, text, *children, tail = space()):
    attr_str = ''.join(f' {k}="{v}"' for k, v in attrib.items())
    description = f'<{tag}{attr_str}>{text or ""}{"..." if children else ""}</{tag}>'

    return described_as(
        description,
        all_of(
            described_as(
                description,
                has_properties(tag = tag, attrib = has_entries(attrib), text = text, tail = tail)),
            contains_exactly(*children)))
