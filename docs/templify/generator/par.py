"""
Module for generating paragraph (Par) XML elements.
Handles creation of paragraph structures with styles and spans.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
from templify.utils.logger_setup import setup_logger
import logging

# Initialize logger
logger = setup_logger(__name__, log_level=logging.INFO)

class AlignEnum(Enum):
    """Text alignment options"""
    LEFT = "LEFT"
    CENTER = "CENTER"
    RIGHT = "RIGHT"
    JUSTIFY = "JUSTIFY"

class BreakTypeEnum(Enum):
    """Break type options"""
    NONE = "none"  # Do not care
    PAGE = "page"  # Produce a page break if current page is not empty
    PAGE_FORCED = "page_forced"  # Produce a page break even if current page is empty
    COLUMN = "column"  # Produce a new column in a multiple column container formatting

class TextDirectionEnum(Enum):
    """Text direction options"""
    LTR = "LTR"  # Left to right
    RTL = "RTL"  # Right to left

class LineSpacingTypeEnum(Enum):
    """Line spacing type options"""
    FIXED = "FIXED"
    MULTIPLE = "MULTIPLE"
    MINIMUM = "MINIMUM"

class SpacingResolutionEnum(Enum):
    """Spacing resolution options"""
    POINTS = "POINTS"
    LINES = "LINES"

class LineTypeEnum(Enum):
    """Line type options"""
    NONE = "none"
    DASHED = "dashed"
    DOTTED = "dotted"
    SOLID = "solid"  # Single solid line
    DOUBLE = "double"  # Two solid lines
    TRIPLE = "triple"  # Three solid lines
    FOUR = "four"  # Four solid lines

class BackgroundThroughSpacingEnum(Enum):
    """Background through spacing options"""
    NONE = "NONE"
    ALL = "ALL"
    BEFORE = "BEFORE"
    AFTER = "AFTER"

class NextCaseCorrectionEnum(Enum):
    """Next case correction options"""
    NONE = "NONE"
    UPPER = "UPPER"
    LOWER = "LOWER"
    TITLE = "TITLE"

class RoleTypeEnum(Enum):
    """Role type options"""
    NONE = "NONE"
    HEADING = "HEADING"
    FOOTNOTE = "FOOTNOTE"
    ENDNOTE = "ENDNOTE"
    PAGE_NUMBER = "PAGE_NUMBER"
    PAGE_COUNT = "PAGE_COUNT"

class AlignmentInParentEnum(Enum):
    """Element alignment within its parent"""
    FIRST = "first"  # Align to the left in horizontal direction or to the top in vertical direction
    CENTER = "center"  # Center the object in the available space
    LAST = "last"  # Align to the right in horizontal direction or to the bottom in vertical direction

class NumberingFormatEnum(Enum):
    """Numbering format options"""
    ARABIC = "ARABIC"
    ROMAN_UPPER = "ROMAN_UPPER"
    ROMAN_LOWER = "ROMAN_LOWER"
    ALPHA_UPPER = "ALPHA_UPPER"
    ALPHA_LOWER = "ALPHA_LOWER"

@dataclass
class LineStyle:
    """Represents a line style with width, color and type"""
    width: Optional[str] = None  # e.g., "1pt"
    color: Optional[str] = None  # e.g., "#000000"
    style: Optional[LineTypeEnum] = None

@dataclass
class Spacing:
    """Represents spacing with value and resolution"""
    value: str  # e.g., "12pt", "1em"
    resolution: Optional[SpacingResolutionEnum] = None

@dataclass
class Indents:
    """Represents indentation settings with units"""
    top: Optional[str] = None  # e.g., "12pt"
    right: Optional[str] = None
    bottom: Optional[str] = None
    left: Optional[str] = None

@dataclass
class Borders:
    """Represents border settings with line styles"""
    top: Optional[LineStyle] = None
    right: Optional[LineStyle] = None
    bottom: Optional[LineStyle] = None
    left: Optional[LineStyle] = None

@dataclass
class LineSpacing:
    """Represents line spacing settings"""
    type: Optional[LineSpacingTypeEnum] = None
    value: Optional[str] = None  # Value with unit based on type

@dataclass
class Tab:
    """Represents a single tab stop"""
    position: str
    alignment: str = "LEFT"
    leader: Optional[str] = None

@dataclass
class Tabs:
    """Represents a collection of tab stops"""
    tabs: List[Tab] = field(default_factory=list)

@dataclass
class SpanStyle:
    """Represents a span style"""
    parent_name: Optional[str] = None
    bold: bool = False
    italic: bool = False
    underline: bool = False
    color: Optional[str] = None
    font_size: Optional[str] = None
    font_family: Optional[str] = None
    background_color: Optional[str] = None
    margin: Optional[Indents] = None
    padding: Optional[Indents] = None
    border: Optional[Borders] = None
    space_before: Optional[Spacing] = None
    space_after: Optional[Spacing] = None
    background_through_spacing: Optional[BackgroundThroughSpacingEnum] = None
    font_style: Optional[str] = None
    text_color: Optional[str] = None
    base_font_size: Optional[str] = None
    char_height: Optional[str] = None
    next_case_correction: Optional[NextCaseCorrectionEnum] = None
    ignore_case_correction: Optional[bool] = None
    hyphenation: Optional[bool] = None
    spellchecking: Optional[bool] = None
    language: Optional[str] = None
    decimal_formats: Optional[str] = None
    reduce_multiple_blanks: Optional[bool] = None
    role: Optional[RoleTypeEnum] = None
    hyperlink_underline: Optional[bool] = None
    hyperlink_color: Optional[str] = None
    wrap: Optional[bool] = None
    marker_name: Optional[str] = None
    page_number_pattern: Optional[str] = None
    page_number_format: Optional[NumberingFormatEnum] = None
    page_count_pattern: Optional[str] = None
    page_count_format: Optional[NumberingFormatEnum] = None
    hidden: Optional[bool] = None
    direction: Optional[TextDirectionEnum] = None

@dataclass
class ParStyle:
    """Represents paragraph style settings"""
    parent_name: Optional[str] = None  # For parentName attribute
    additional_css_classes: Optional[str] = None
    background_color: Optional[str] = None
    margin: Optional[Indents] = None
    padding: Optional[Indents] = None
    border: Optional[Borders] = None
    space_before: Optional[Spacing] = None
    space_after: Optional[Spacing] = None
    background_through_spacing: Optional[str] = None
    keep_with_next: Optional[bool] = None
    keep_with_previous: Optional[bool] = None
    keep_together: Optional[bool] = None
    break_before: Optional[BreakTypeEnum] = None
    break_after: Optional[BreakTypeEnum] = None
    vertical_position: Optional[AlignmentInParentEnum] = None
    orphans: Optional[int] = None
    widows: Optional[int] = None
    next_case_correction: Optional[str] = None
    ignore_case_correction: Optional[bool] = None
    align: Optional[AlignEnum] = None
    left_indent: Optional[str] = None
    right_indent: Optional[str] = None
    first_indent: Optional[str] = None
    line_spacing: Optional[LineSpacing] = None
    tabs: Optional[Tabs] = None
    next_style: Optional[str] = None
    allow_vertical_truncation: Optional[int] = None
    role: Optional[str] = None
    wrap: Optional[bool] = None
    direction: Optional[TextDirectionEnum] = None
    span_styles: List[SpanStyle] = field(default_factory=list)

@dataclass
class Span:
    """Represents a span element with text or data reference"""
    text: Optional[str] = None
    data_ref: Optional[str] = None
    style: Optional[SpanStyle] = None

@dataclass
class ScriptableLanguage:
    """Represents a language setting that can be scripted"""
    value: Optional[str] = None
    script: Optional[str] = None

@dataclass
class Par:
    """Represents a paragraph element"""
    style: Optional[ParStyle] = None
    language: Optional[ScriptableLanguage] = None
    spans: List[Span] = field(default_factory=list)

def create_line_style_xml(style: LineStyle) -> str:
    """Generate XML for line style settings"""
    if not style:
        return ""
        
    attrs = []
    if style.width:
        attrs.append(f'width="{style.width}"')
    if style.color:
        attrs.append(f'color="{style.color}"')
    if style.style:
        attrs.append(f'style="{style.style.value}"')
        
    if not attrs:
        return ""
        
    return f'<LineStyle {" ".join(attrs)}/>'

def create_borders_xml(borders: Borders) -> str:
    """Generate XML for border settings"""
    if not borders:
        return ""
        
    elements = []
    if borders.top:
        elements.append(f'<Top>{create_line_style_xml(borders.top)}</Top>')
    if borders.right:
        elements.append(f'<Right>{create_line_style_xml(borders.right)}</Right>')
    if borders.bottom:
        elements.append(f'<Bottom>{create_line_style_xml(borders.bottom)}</Bottom>')
    if borders.left:
        elements.append(f'<Left>{create_line_style_xml(borders.left)}</Left>')
        
    if not elements:
        return ""
        
    return f'''<Border>
    {"".join(elements)}
</Border>'''

def create_span_style_xml(style: SpanStyle) -> str:
    """Generate XML for span style settings"""
    if not style:
        return ""
        
    elements = []
    
    # Add parentName attribute if present
    parent_name_attr = f' parentName="{style.parent_name}"' if style.parent_name else ""
    
    # Basic style properties
    if style.background_color:
        elements.append(f'<BackgroundColor>{style.background_color}</BackgroundColor>')
        
    # Margin and padding
    if style.margin:
        elements.append(f'''<Margin>
    <Top>{style.margin.top}</Top>
    <Right>{style.margin.right}</Right>
    <Bottom>{style.margin.bottom}</Bottom>
    <Left>{style.margin.left}</Left>
</Margin>''')
    if style.padding:
        elements.append(f'''<Padding>
    <Top>{style.padding.top}</Top>
    <Right>{style.padding.right}</Right>
    <Bottom>{style.padding.bottom}</Bottom>
    <Left>{style.padding.left}</Left>
</Padding>''')
        
    # Border
    if style.border:
        elements.append(create_borders_xml(style.border))
        
    # Spacing
    if style.space_before:
        resolution_attr = f' resolution="{style.space_before.resolution.value}"' if style.space_before.resolution else ""
        elements.append(f'<SpaceBefore{resolution_attr}>{style.space_before.value}</SpaceBefore>')
    if style.space_after:
        resolution_attr = f' resolution="{style.space_after.resolution.value}"' if style.space_after.resolution else ""
        elements.append(f'<SpaceAfter{resolution_attr}>{style.space_after.value}</SpaceAfter>')
        
    # Font properties
    if style.font_size:
        elements.append(f'<FontSize>{style.font_size}</FontSize>')
    if style.font_family:
        elements.append(f'<FontFamily>{style.font_family}</FontFamily>')
    if style.font_style:
        elements.append(f'<FontStyle>{style.font_style}</FontStyle>')
    if style.text_color:
        elements.append(f'<TextColor>{style.text_color}</TextColor>')
    if style.base_font_size:
        elements.append(f'<BaseFontSize>{style.base_font_size}</BaseFontSize>')
    if style.char_height:
        elements.append(f'<CharHeight>{style.char_height}</CharHeight>')
        
    # Case correction
    if style.next_case_correction:
        elements.append(f'<NextCaseCorrection>{style.next_case_correction.value}</NextCaseCorrection>')
    if style.ignore_case_correction is not None:
        elements.append(f'<IgnoreCaseCorrection>{str(style.ignore_case_correction).lower()}</IgnoreCaseCorrection>')
        
    # Text properties
    if style.hyphenation is not None:
        elements.append(f'<Hyphenation>{str(style.hyphenation).lower()}</Hyphenation>')
    if style.spellchecking is not None:
        elements.append(f'<Spellchecking>{str(style.spellchecking).lower()}</Spellchecking>')
    if style.language:
        elements.append(f'<Language>{style.language}</Language>')
    if style.reduce_multiple_blanks is not None:
        elements.append(f'<ReduceMultipleBlanks>{str(style.reduce_multiple_blanks).lower()}</ReduceMultipleBlanks>')
        
    # Role and direction
    if style.role:
        elements.append(f'<Role>{style.role.value}</Role>')
    if style.direction:
        elements.append(f'<Direction>{style.direction.value}</Direction>')
        
    # Hyperlink properties
    if style.hyperlink_underline is not None:
        elements.append(f'<HyperlinkUnderline>{str(style.hyperlink_underline).lower()}</HyperlinkUnderline>')
    if style.hyperlink_color:
        elements.append(f'<HyperlinkColor>{style.hyperlink_color}</HyperlinkColor>')
        
    # Page number properties
    if style.page_number_pattern:
        elements.append(f'<PageNumberPattern>{style.page_number_pattern}</PageNumberPattern>')
    if style.page_number_format:
        elements.append(f'<PageNumberFormat>{style.page_number_format.value}</PageNumberFormat>')
    if style.page_count_pattern:
        elements.append(f'<PageCountPattern>{style.page_count_pattern}</PageCountPattern>')
    if style.page_count_format:
        elements.append(f'<PageCountFormat>{style.page_count_format.value}</PageCountFormat>')
        
    # Other properties
    if style.wrap is not None:
        elements.append(f'<Wrap>{str(style.wrap).lower()}</Wrap>')
    if style.marker_name:
        elements.append(f'<MarkerName>{style.marker_name}</MarkerName>')
    if style.hidden is not None:
        elements.append(f'<Hidden>{str(style.hidden).lower()}</Hidden>')
        
    if not elements:
        return f'<Style{parent_name_attr}/>'
        
    return f'''<Style{parent_name_attr}>
    {"".join(elements)}
</Style>'''

def create_span_xml(span: Span) -> str:
    """Generate XML for a span element"""
    style_xml = create_span_style_xml(span.style) if span.style else ""
    
    if span.data_ref:
        return f'''<Span>
    {style_xml}
    <Data>{span.data_ref}</Data>
</Span>'''
    elif span.text:
        return f'''<Span>
    {style_xml}
    <Text>{span.text}</Text>
</Span>'''
    else:
        return ""

def create_par_style_xml(style: ParStyle) -> str:
    """Generate XML for paragraph style settings"""
    if not style:
        return ""
        
    elements = []
    
    # Add parentName attribute if present
    parent_name_attr = f' parentName="{style.parent_name}"' if style.parent_name else ""
    
    # Basic style properties
    if style.additional_css_classes:
        elements.append(f'<AdditionalCssClasses>{style.additional_css_classes}</AdditionalCssClasses>')
    if style.background_color:
        elements.append(f'<BackgroundColor>{style.background_color}</BackgroundColor>')
    if style.align:
        elements.append(f'<Align>{style.align.value}</Align>')
        
    # Spacing with resolution
    if style.space_before:
        resolution_attr = f' resolution="{style.space_before.resolution.value}"' if style.space_before.resolution else ""
        elements.append(f'<SpaceBefore{resolution_attr}>{style.space_before.value}</SpaceBefore>')
    if style.space_after:
        resolution_attr = f' resolution="{style.space_after.resolution.value}"' if style.space_after.resolution else ""
        elements.append(f'<SpaceAfter{resolution_attr}>{style.space_after.value}</SpaceAfter>')
        
    # Break properties
    if style.break_before:
        elements.append(f'<BreakBefore>{style.break_before.value}</BreakBefore>')
    if style.break_after:
        elements.append(f'<BreakAfter>{style.break_after.value}</BreakAfter>')
    if style.vertical_position:
        elements.append(f'<VerticalPosition>{style.vertical_position.value}</VerticalPosition>')
    if style.direction:
        elements.append(f'<Direction>{style.direction.value}</Direction>')
        
    # Indentation
    if style.left_indent:
        elements.append(f'<LeftIndent>{style.left_indent}</LeftIndent>')
    if style.right_indent:
        elements.append(f'<RightIndent>{style.right_indent}</RightIndent>')
    if style.first_indent:
        elements.append(f'<FirstIndent>{style.first_indent}</FirstIndent>')
        
    # Line spacing with type
    if style.line_spacing:
        type_attr = f' type="{style.line_spacing.type.value}"' if style.line_spacing.type else ""
        value_attr = f' value="{style.line_spacing.value}"' if style.line_spacing.value else ""
        elements.append(f'<LineSpacing{type_attr}{value_attr}/>')
        
    # Keep properties
    if style.keep_with_next is not None:
        elements.append(f'<KeepWithNext>{str(style.keep_with_next).lower()}</KeepWithNext>')
    if style.keep_with_previous is not None:
        elements.append(f'<KeepWithPrevious>{str(style.keep_with_previous).lower()}</KeepWithPrevious>')
    if style.keep_together is not None:
        elements.append(f'<KeepTogether>{str(style.keep_together).lower()}</KeepTogether>')
        
    # Border
    if style.border:
        elements.append(create_borders_xml(style.border))
        
    if not elements:
        return f'<Style{parent_name_attr}/>'
        
    return f'''<Style{parent_name_attr}>
    {"".join(elements)}
</Style>'''

def create_par_xml(par: Par) -> str:
    """Generate XML for a paragraph element"""
    style_xml = create_par_style_xml(par.style) if par.style else ""
    language_xml = f'''<Language>
    <Value>{par.language.value}</Value>
</Language>''' if par.language and par.language.value else ""
    
    spans_xml = "\n".join(create_span_xml(span) for span in par.spans)
    
    return f'''<Par>
    {style_xml}
    {language_xml}
    {spans_xml}
</Par>'''

def create_pars_xml(pars: List[Par]) -> str:
    """Generate XML for multiple paragraphs"""
    return "\n".join(create_par_xml(par) for par in pars)

def main():
    """Example usage of the paragraph generation functions."""
    # Create a paragraph with style and spans
    style = ParStyle(
        align=AlignEnum.LEFT,
        space_before=Spacing(value="12pt", resolution=SpacingResolutionEnum.POINTS),
        space_after=Spacing(value="12pt", resolution=SpacingResolutionEnum.POINTS),
        line_spacing=LineSpacing(type=LineSpacingTypeEnum.MULTIPLE, value="1.2"),
        border=Borders(
            top=LineStyle(width="1pt", color="#000000", style=LineTypeEnum.SOLID),
            bottom=LineStyle(width="1pt", color="#000000", style=LineTypeEnum.SOLID)
        ),
        break_before=BreakTypeEnum.NONE,
        break_after=BreakTypeEnum.NONE
    )
    
    # Create a span with style
    span_style = SpanStyle(
        font_family="Arial",
        font_size="12pt",
        text_color="#000000",
        background_color="#FFFFFF",
        margin=Indents(top="2pt", bottom="2pt"),
        padding=Indents(left="4pt", right="4pt"),
        border=Borders(
            bottom=LineStyle(width="1pt", color="#CCCCCC", style=LineTypeEnum.SOLID)
        ),
        direction=TextDirectionEnum.LTR,
        role=RoleTypeEnum.NONE
    )
    
    par = Par(
        style=style,
        language=ScriptableLanguage(value="de"),
        spans=[
            Span(text="Hello ", style=span_style),
            Span(data_ref="$document.FRW060.Dialog.Variable1", style=span_style),
            Span(text=" World!", style=span_style)
        ]
    )
    
    # Generate XML
    xml = create_par_xml(par)
    logger.info("Generated paragraph XML:")
    logger.info(xml)

if __name__ == "__main__":
    main()
