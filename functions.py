# A python script for generating SLDs
# from ESRI ArcGIS map document (.mxd) files
# Naghshara CO.

try:
    import os
    import json
    # import arcpy
    import xmltodict
    from xml.parsers.expat import ExpatError
    from shutil import copyfile
    import zipfile
    from colorutils import hsv_to_rgb, rgb_to_hex
    from PIL import Image, ImageDraw, ImageFont
    import matplotlib.font_manager
    import pylab as pl
    from matplotlib.font_manager import findfont
    import logging
    import base64
    import random
    import string
    from datetime import datetime
    import codecs
    import glob
    
except Exception as e:
    print '\n====================================='
    print 'Failed to run script!'
    print 'Some of the requirements are missing.'
    print 'More Information =>'
    print e
    raise Exception("Terminated")

logging.basicConfig(filename="log.log", level=logging.INFO)

def now_date_time():
    try:
        now = datetime.now()
        return now.strftime("%Y.%m.%d %H.%M.%S")
    except Exception as e:
        print e
        raise('ERROR!')
    
def convert2pix(size):
    if size.isdigit():
        return int(size) * 1.33
    else:
        return float(size) * 1.33

def is_exist(_path_):
    if os.path.exists(_path_):
        return True
    else:
        return False

def copy_file(_path_, _dist_, _name_):
    try:
        _path_ += '\\' + _name_
        _dist_ += '\\' + _name_
        if is_exist(_dist_):
            return _dist_
        copyfile(_path_, _dist_)
        return _dist_
    except:
        return False

def extract_wrm(_path_):
    try:
        if not is_exist(_path_):
            raise Exception('WRM was not found. %s' % _path_)

        msd_dir, msd_name = os.path.split(_path_)
        res_dir = os.path.abspath(os.path.join(msd_dir, os.pardir))
        res_dir = os.path.join(res_dir, "%s (%s)" % (msd_name.replace('.msd',''), now_date_time()))

        if not is_exist(res_dir):
            os.makedirs(res_dir)

        copy_dir = copy_file(msd_dir, res_dir, msd_name)
        pre, ext = os.path.splitext(copy_dir)

        zip_dir = pre + '.zip'
        if not is_exist(zip_dir):
            os.rename(copy_dir, pre + '.zip')

        unzip_dir = os.path.split(zip_dir)[0]
        with zipfile.ZipFile(zip_dir, 'r') as zip_ref:
            zip_ref.extractall(unzip_dir)

        return unzip_dir

    except:
        return False

def parse_xml(_path_):
    if not is_exist(_path_):
        raise Exception('Unable to fine <<xml>> file! %s' % _path_)

    xml_file = open(_path_)

    print _path_

    try:
        ordered_dict = xmltodict.parse(xml_file)
        return json.loads(json.dumps(ordered_dict))
    except (xmltodict.ParsingInterrupted, ExpatError):
        raise Exception("Unable parse <<xml>> file!")

def random_string(size):
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(size))

def find_font(font_family):
    font_dir = ''
    sys_fonts = matplotlib.font_manager.fontManager.ttflist
    for font in sys_fonts:
        if font.name == font_family:
            font_dir = font.fname
            break

    if not font_dir:
        for font in sys_fonts:
            if font.name == 'NaghshAra_V1':
                font_dir = font.fname
                break
        # la = pl.matplotlib.font_manager.FontManager()
        # lu = pl.matplotlib.font_manager.FontProperties(family = font_family)
        # la.findfont(lu)
        # print sys_fonts
        # raise Exception("Unable to find font %s." % font_family)
    

    if not is_exist(font_dir):
        raise Exception("Unable to find font %s." % font_dir)

    return font_dir.replace('\\', '//')

def cmyk_to_rgb(c,m,y,k):
    r = 255*(1.0-(c+k)/float(100))
    g = 255*(1.0-(m+k)/float(100))
    b = 255*(1.0-(y+k)/float(100))
    return r,g,b

def generate_hex_code(color_object):
    color_pallet = color_object['@xsi:type']
    if 'CMYK' in color_pallet:
        c = int(color_object['C'])
        m = int(color_object['M'])
        y = int(color_object['Y'])
        k = int(color_object['K'])
        rgb_color = cmyk_to_rgb(c,m,y,k)
        r = int(round(rgb_color[0]))
        g = int(round(rgb_color[1]))
        b = int(round(rgb_color[2]))
        return rgb_to_hex((r, g, b))

    elif 'RGB' in color_pallet:
        r = int(color_object['R'])
        g = int(color_object['G'])
        b = int(color_object['B'])
        return rgb_to_hex((r, g, b))

    elif 'HSV' in color_pallet:
        h = int(color_object['H'])
        s = float(color_object['S'])/100
        v = float(color_object['V'])/100
        rgb_color = hsv_to_rgb((h, s, v))
        
        r = int(round(rgb_color[0]))
        g = int(round(rgb_color[1]))
        b = int(round(rgb_color[2]))
        return rgb_to_hex((r, g, b))
    
    else:
        raise Exception("Unhandled type of color pallet!")

def generate_css_parameter(name,value):
    if name == 'font-size' or name == 'stroke-width':
        value = convert2pix(value)
    else:
        value = value.strip().lower()

    return '<CssParameter name="%s">%s</CssParameter>' % (name, value)

def generate_symbol_mark_wellknown(name, index):
    return '<WellKnownName>ttf://%s#%s</WellKnownName>' % (name, index)

def generate_symbol_mark_size(size):
    # size = int(size) * 1.33
    size = convert2pix(size)
    return '<Size>%s</Size>' % size

def generate_fill_tag(value):
    return '<Fill>%s</Fill>' % generate_css_parameter('fill', value)

def generate_character_marker(font_name, font_index, fill, font_size):
    result = ''
    result += generate_symbol_mark_wellknown(font_name,font_index)
    result += generate_fill_tag(fill)
    return '<Mark>%s</Mark>%s' % (result, generate_symbol_mark_size(font_size))

def generate_symbol_external_graphic(sym_name, sym_color, sym_size, font_family, font_index):
    # sym_size = int(sym_size) * 1.33
    sym_size = convert2pix(sym_size)
    sys_fonts = matplotlib.font_manager.fontManager.ttflist
    for font in sys_fonts:
        if font.name == font_family:
            font_dir = font.fname
            break
    
    if not is_exist(font_dir):
        raise Exception("Unable to find font %s." % font_dir)
    
    # sym_size = int(sym_size)
    sym_size = convert2pix(sym_size)
    sym_char =chr(int(font_index))
    image = Image.new('RGBA', (sym_size, sym_size), (0, 0, 0, 0))
    try:
        font = ImageFont.truetype(font_dir, size=sym_size)
        drawing = ImageDraw.Draw(image)
        w, h = drawing.textsize((sym_char), font=font)
        drawing.text(
            ((sym_size-w)/2, (sym_size-h)/2),
            sym_char,
            fill=sym_color,
            font=font
        )
        symbol_dir = './msd/results/new_sld/images/%s.png' % sym_name
        image.save(symbol_dir)
        return '<Graphic><ExternalGraphic><OnlineResource xlink:type="simple" xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="%s"/><Format>image/png</Format></ExternalGraphic><Size>%s</Size></Graphic>' % (symbol_dir, sym_size)
    except:
        raise Exception("Exception in creating symbol from text.")

def manage_character_marker(character_marker_dict):
    result = ''
    # symbol_character_font = find_font(character_marker_dict['FontFamilyName'])
    symbol_character_font = character_marker_dict['FontFamilyName']
    symbol_character_index = character_marker_dict['CharacterIndex']
    symbol_character_size = character_marker_dict['Size']

    if character_marker_dict['OffsetX'] != '0':
        symbol_offset_x = convert2pix(character_marker_dict['OffsetX'])
    
    if character_marker_dict['OffsetY'] != '0':
        symbol_offset_y = convert2pix(character_marker_dict['OffsetY'])

    symbol_shape_type = character_marker_dict['Symbol']['@xsi:type']
    if 'Polygon' in symbol_shape_type:
                    
        symbol_shapes = character_marker_dict['Symbol']['SymbolLayers']
        if not isinstance(symbol_shapes, list):
            tmp = []
            tmp.append(symbol_shapes)
            symbol_shapes = tmp

        for symbol_shape in symbol_shapes:
            symbol_shape = symbol_shape['CIMSymbolLayer']

            if 'Pattern' in symbol_shape:
                pattern_color = symbol_shape['Pattern']['Color']
                symbol_character_fill = generate_hex_code(pattern_color)
                character_marker = generate_character_marker(
                    symbol_character_font,
                    symbol_character_index,
                    symbol_character_fill,
                    symbol_character_size)

                result += '<Graphic>%s</Graphic>' % character_marker

            else:
                raise Exception("Managing character marker => Unhandled symbol shape <<%s>>" % symbol_shape)

    else:
        raise Exception("Managing character marker => Unhandled symbol shape type <<%s>>" % symbol_shape_type)

    return result

def manage_simple_marker(simple_marker_dict):
    result = ''

    marker_shape = simple_marker_dict['Type'].lower()
    if marker_shape not in ['square', 'circle', 'triangle', 'star', 'cross', 'x']:
        marker_shape = 'circle'

    marker_size = simple_marker_dict['Size']
    marker_fill_color = simple_marker_dict['FillColor']
    marker_outline_color = simple_marker_dict['OutlineColor']
    marker_outline_width = simple_marker_dict['OutlineWidth']
    result += '' +\
        '<Graphic>' +\
        '<Mark>' +\
            '<WellKnownName>%s</WellKnownName>' % marker_shape +\
            generate_fill_tag(generate_hex_code(marker_fill_color)) +\
                '<Stroke>' +\
                    generate_css_parameter('stroke', generate_hex_code(marker_outline_color)) +\
                    generate_css_parameter('stroke-width', marker_outline_width) +\
                    generate_css_parameter('stroke', generate_hex_code(marker_outline_color)) +\
                '</Stroke>' +\
            '</Mark>' +\
            generate_symbol_mark_size(marker_size) +\
        '</Graphic>'
    
    return result

def manage_placed_point_layer(placed_point_layer_dict):
    result = ''

    point_symbols = placed_point_layer_dict['PointSymbols']
    if not isinstance(point_symbols, list):
        tmp = []
        tmp.append(point_symbols)
        point_symbols = tmp

    for point_symbol in point_symbols:
        
        symbols = point_symbol['CIMPointSymbol']['SymbolLayers']
        if not isinstance(symbols, list):
            tmp = []
            tmp.append(symbols)
            symbols = tmp

        for symbol in symbols:
            symbol = symbol['CIMSymbolLayer']
            symbol_type = symbol['@xsi:type']
            
            if 'CharacterMarker' in symbol_type:
                result += '<GraphicStroke>%s</GraphicStroke>' % manage_character_marker(symbol)

            # [ignored part]
            elif 'VectorMarker' in symbol_type:
                result = ''
                        
    return result

def manage_filled_stroke_layer(filled_stroke_layer_dict):
    result_stk = ''
    result_pdc = ''
    
    sym_stroke_linecap = filled_stroke_layer_dict['CapStyle']
    if sym_stroke_linecap != 'false':
        result_stk += generate_css_parameter('stroke-linecap', sym_stroke_linecap)

    sym_stroke_linejoin = filled_stroke_layer_dict['JoinStyle']
    if sym_stroke_linejoin != 'false':
        result_stk += generate_css_parameter('stroke-linejoin', sym_stroke_linejoin)

    sym_stroke_width = filled_stroke_layer_dict['Width']
    result_stk += generate_css_parameter('stroke-width', sym_stroke_width)

    if 'Effects' in filled_stroke_layer_dict:
        tag_effect = filled_stroke_layer_dict['Effects']
        effect_type = tag_effect['@xsi:type']
        if 'CIMGeometricEffect' in effect_type:

            if not isinstance(tag_effect['CIMGeometricEffect'], list):
                tmp = []
                tmp.append(tag_effect['CIMGeometricEffect'])
                tag_effect['CIMGeometricEffect'] = tmp

            for effect in tag_effect['CIMGeometricEffect']:
                geometric_effect_type = effect['@xsi:type']
                if 'GeometricEffectDashes' in geometric_effect_type:
                    
                    sym_stroke_dashoffset = effect['CustomEndingOffset']
                    result_stk += generate_css_parameter('stroke-dashoffset', sym_stroke_dashoffset)

                    stroke_dasharray_pattern = effect['DashTemplate']
                    sym_stroke_dasharray = ''
                    for dasharray in stroke_dasharray_pattern['Double']:
                        sym_stroke_dasharray += dasharray + ' '
                    result_stk += generate_css_parameter('stroke-dasharray', sym_stroke_dasharray.strip())
                
                elif 'GeometricEffectOffset' in geometric_effect_type:
                    result_pdc = '<PerpendicularOffset>%s</PerpendicularOffset>' % effect['Offset']

                else:
                    raise Exception("!!!! Different Geometric Effect Type Was Found => %s !!!!" % geometric_effect_type)
        
        else:
            raise Exception("!!!! Different Effect Type Was Found => %s !!!!" % effect_type)

    if 'Pattern' in filled_stroke_layer_dict:
        tag_pattern = filled_stroke_layer_dict['Pattern']
        pattern_type = tag_pattern['@xsi:type']

        if 'SolidPattern' in pattern_type:
            
            if 'Color' in tag_pattern:
                pattern_color = tag_pattern['Color']
                result_stk += generate_css_parameter('stroke', generate_hex_code(pattern_color))

                if int(pattern_color['Alpha']) < 100:
                    pattern_opacity = str(int(pattern_color['Alpha']) / 100)
                    result_stk += generate_css_parameter('stroke-opacity', pattern_opacity)
        else:
            raise Exception("!!!! Different Pattern Type Was Found. => %s !!!!" % effect_type)

    result = {}
    result['result_stk'] = result_stk
    result['result_pdc'] = result_pdc
    
    return result

def manage_graphic_marker(graphic_marker_dict):
    result = ''
    marker_layers = graphic_marker_dict['CIMSymbolLayer']
    if not isinstance(marker_layers, list):
        tmp = []
        tmp.append(marker_layers)
        marker_layers = tmp

    for marker_layer in marker_layers:
        marker_layer_type = marker_layer['@xsi:type']

        if 'SimpleMarker' in marker_layer_type:
            # result += manage_simple_marker(marker_layer)

            marker_shape = marker_layer['Type'].lower()
            if marker_shape not in ['square', 'circle', 'triangle', 'star', 'cross', 'x']:
                marker_shape = 'circle'
            marker_size = marker_layer['Size']
            marker_color = marker_layer['FillColor']
            result += '' +\
                '<GraphicFill>' +\
                    '<Graphic>' +\
                        '<Mark>' +\
                            '<WellKnownName>%s</WellKnownName>' % marker_shape +\
                            generate_fill_tag(generate_hex_code(marker_color)) +\
                        '</Mark>' +\
                        generate_symbol_mark_size(marker_size) +\
                    '</Graphic>' +\
                '</GraphicFill>'
                

        elif 'CharacterMarker' in marker_layer_type:
            result += '<GraphicFill>%s</GraphicFill>' % manage_character_marker(marker_layer)

        # [ignored part]
        elif 'PictureMarker' in marker_layer_type:
            result += ''

        else:
            raise Exception("!!!! Different Marker Pattern :: <<%s>> :: Unhandled !!!!" % marker_layer_type)
    
    return result

def manage_hatch_pattern_layer(hatch_pattern_layer_dict):
    result = ''
    hatch_layers = hatch_pattern_layer_dict['CIMSymbolLayer']
    if not isinstance(hatch_layers, list):
        tmp = []
        tmp.append(hatch_layers)
        hatch_layers = tmp

    for hatch_layer in hatch_layers:
        hatch_layer_type = hatch_layer['@xsi:type']

        if 'FilledStroke' in hatch_layer_type:
            result += '' +\
                '<Mark>' +\
                    '<WellKnownName>%s</WellKnownName>' % 'shape://slash' +\
                    '<Stroke>%s</Stroke>' % manage_filled_stroke_layer(hatch_layer)['result_stk'] +\
                '</Mark>'

        else:
            raise Exception("!!!! Different Hatch Pattern :: <<%s>> :: Unhandled !!!!" % hatch_layer_type)


    return result

def generate_text_symbolizer(label_classes):
    text_symbolizer = ''
    result = ''

    if not isinstance(label_classes, list):
        tmp = []
        tmp.append(label_classes)
        label_classes = tmp
    
    font_family = ''
    font_size = ''
    font_style = ''
    font_weight = ''
    font_color = ''
    label_halo_tag = ''

    for i in range(0, len(label_classes)):
        label_class = label_classes[i]
        max_scale = label_class['MinimumScale']
        min_scale = label_class['MaximumScale']

        label = label_class['TextSymbol']['Symbol']

        label_font_family =  label['FontFamilyName']
        label_font_size = convert2pix(label['Height'])
        label_font_style = label['FontStyleName'].lower()
        label_font_weight = label['FontEffects'].lower()

        logging.info('Font family <<%s>> is being used at scale <<1:%s>>!' % (label_font_family, max_scale))

        if 'Color' not in label['Symbol']['SymbolLayers']['CIMSymbolLayer']['Pattern']:
            label_font_color_hex = '#000000'
        else:
            label_font_color = label['Symbol']['SymbolLayers']['CIMSymbolLayer']['Pattern']['Color']
            label_font_color_hex = generate_hex_code(label_font_color)

        if i == 0:
            label_expression = label_class['Expression']
            label_expression_engine = label_class['ExpressionEngine']

            if label_expression_engine == 'VBScript' or label_expression_engine == 'Python':
                if label_expression_engine == 'Python':
                    q= 1
                label_tag = ''
                for item in label_expression.split('+'):
                    if '[' in item and ']' in item:
                        label_property = item.replace('[','').replace(']','').strip()
                        label_tag += '<ogc:PropertyName>%s</ogc:PropertyName>' % label_property
                    else:
                        label_literal = item.replace('"','').strip()
                        label_tag += '<ogc:Literal>%s</ogc:Literal>' % label_literal
                result += '<Label>%s</Label>' % label_tag

            else:
                raise Exception("Unhandled type of expression => <<%s>> " % label_expression_engine)
            
            halo_size = convert2pix(label['HaloSize'])
            if halo_size:
                halo_properties = label['HaloSymbol']['SymbolLayers']['CIMSymbolLayer']
                if not isinstance(halo_properties, list):
                    tmp = []
                    tmp.append(halo_properties)
                    halo_properties = tmp
                for halo in halo_properties:
                    halo_type = halo['@xsi:type']
                    if 'CIMFilledStroke' in halo_type:
                        if 'Color' in halo['Pattern']:
                            label_halo_color = halo['Pattern']['Color']
                            label_halo_color_hex = generate_hex_code(label_halo_color)
                            label_halo_tag = ''+\
                                '<Halo>' +\
                                    '<Radius>%s</Radius>%s' % (halo_size, generate_fill_tag(label_halo_color_hex)) +\
                                '</Halo>'
                        else:
                            label_halo_tag = ''

            font_family += '<ogc:Literal>%s</ogc:Literal>' % label_font_family
            font_size += '<ogc:Literal>%s</ogc:Literal>' % label_font_size
            font_style += '<ogc:Literal>%s</ogc:Literal>' % label_font_style
            font_weight += '<ogc:Literal>%s</ogc:Literal>' % label_font_weight
            font_color += '<ogc:Literal>%s</ogc:Literal>' % label_font_color_hex
        
        else:
            font_family += '<ogc:Literal>%s</ogc:Literal><ogc:Literal>%s</ogc:Literal>' % (max_scale, label_font_size)
            font_size += '<ogc:Literal>%s</ogc:Literal><ogc:Literal>%s</ogc:Literal>' % (max_scale, label_font_size)
            font_style += '<ogc:Literal>%s</ogc:Literal><ogc:Literal>%s</ogc:Literal>' % (max_scale, label_font_size)
            font_weight += '<ogc:Literal>%s</ogc:Literal><ogc:Literal>%s</ogc:Literal>' % (max_scale, label_font_size)
            font_color += '<ogc:Literal>%s</ogc:Literal><ogc:Literal>%s</ogc:Literal>' % (max_scale, label_font_color_hex)
 
    label_font_family_tag = ''+\
        '<CssParameter name="font-family">' +\
            '<ogc:Function name="Categorize">' +\
                '<ogc:Function name="env">' +\
                    '<ogc:Literal>wms_scale_denominator</ogc:Literal>' +\
                '</ogc:Function>' +\
                font_family +\
            '</ogc:Function>' +\
        '</CssParameter>'
    
    label_font_size_tag = ''+\
        '<CssParameter name="font-size">' +\
            '<ogc:Function name="Categorize">' +\
                '<ogc:Function name="env">' +\
                    '<ogc:Literal>wms_scale_denominator</ogc:Literal>' +\
                '</ogc:Function>' +\
                font_size +\
            '</ogc:Function>' +\
        '</CssParameter>'
    
    label_font_style_tag = ''+\
        '<CssParameter name="font-style">' +\
            '<ogc:Function name="Categorize">' +\
                '<ogc:Function name="env">' +\
                    '<ogc:Literal>wms_scale_denominator</ogc:Literal>' +\
                '</ogc:Function>' +\
                font_style +\
            '</ogc:Function>' +\
        '</CssParameter>'
    
    label_font_weight_tag = ''+\
        '<CssParameter name="font-weight">' +\
            '<ogc:Function name="Categorize">' +\
                '<ogc:Function name="env">' +\
                    '<ogc:Literal>wms_scale_denominator</ogc:Literal>' +\
                '</ogc:Function>' +\
                font_weight +\
            '</ogc:Function>' +\
        '</CssParameter>'

    label_font_color_tag = ''+\
        '<CssParameter name="fill">' +\
            '<ogc:Function name="Categorize">' +\
                '<ogc:Function name="env">' +\
                    '<ogc:Literal>wms_scale_denominator</ogc:Literal>' +\
                '</ogc:Function>' +\
                font_color +\
            '</ogc:Function>' +\
        '</CssParameter>'

    result += '<Font>' + label_font_family_tag + label_font_size_tag + label_font_style_tag + label_font_weight_tag + '</Font>'
    
    # [ignored part]
    result += ''+\
        '<LabelPlacement>' +\
            '<PointPlacement>' +\
                '<Displacement>' +\
                    '<DisplacementX>%s</DisplacementX>' % '0' +\
                    '<DisplacementY>%s</DisplacementY>' % '15' +\
                '</Displacement>' +\
                '<Rotation>%s</Rotation>' % '0' +\
            '</PointPlacement>' +\
        '</LabelPlacement>'

    if label_halo_tag: result += label_halo_tag

    result += '<Fill>' + label_font_color_tag + '</Fill>'
    text_symbolizer += '<TextSymbolizer>%s</TextSymbolizer>' % result
    
    return text_symbolizer

def base2image(image_name, base64_sting):
    if 'data:image/' in base64_sting:
        
        try:
            temp_dir = os.path.dirname(os.path.realpath('tmp.txt')) + '/tmp.txt'
            with codecs.open(temp_dir, encoding='utf-8') as f:
                for line in f:
                    image_dir = line
            
            image_ext = base64_sting.split('data:image/')[1].split(';')[0]
            image_path = '%s/%s.%s' % (image_dir, image_name, image_ext)
        
            image_data = base64.b64decode(base64_sting.split(',')[1])
            with open(image_path, 'wb') as f:
                f.write(image_data)
            return image_path, image_ext

        except:
            raise Exception("Error in creating image file from base64 string")

    else:
        raise Exception("Invalid base64 image URL")

def manage_picture_marker(name, picture_marker_dict):
    image_name = name
    if not name:
        image_name = random_string(40)
    image_dir, image_ext = base2image(image_name, picture_marker_dict['URL'])
    image_size = convert2pix(picture_marker_dict['Size'])
    # image_size = int(picture_marker_dict['Size']) * 1.33
    
    result = '' +\
        '<ExternalGraphic>' +\
            '<OnlineResource xlink:type="simple" xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="file:///%s"/>' % image_dir +\
            '<Format>image/%s</Format>' % image_ext +\
        '</ExternalGraphic>' +\
        '<Size>%s</Size>' % image_size

    return result
        
def purge_project(_path_):
    try:
        os.chdir(_path_)
        for file in glob.glob("*.xml"):
            os.remove(file)
            
        for file in glob.glob("*.zip"):
            os.remove(file)
        
        os.chdir(_path_ + '\\layers')
        for file in glob.glob("*.xml"):
            os.remove(file)
            
    except Exception as e:
        print e
        raise('Error in purging project!')
    


