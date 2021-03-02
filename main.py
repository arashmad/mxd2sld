# -*- coding: utf-8 -*-

try:
    import os
    import json
    import codecs
    import datetime
    import logging

    from functions import *
    from xml.parsers.expat import ExpatError
    from colorutils import hsv_to_rgb, rgb_to_hex

except Exception as e:
    print '\n====================================='
    print 'Failed to run script!'
    print 'Some of the requirements are missing.'
    print 'More Information =>'
    print e
    raise Exception("Terminated")

logging.basicConfig(filename="log.log", level=logging.INFO)

tag_root = '' +\
    '<?xml version="1.0" encoding="UTF-8"?>' +\
    '<StyledLayerDescriptor' +\
        ' version="1.0.0"' +\
        ' xsi:schemaLocation="http://www.opengis.net/sld' +\
        ' http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd"' +\
        ' xmlns="http://www.opengis.net/sld"' +\
        ' xmlns:ogc="http://www.opengis.net/ogc"' +\
        ' xmlns:xlink="http://www.w3.org/1999/xlink"' +\
        ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' +\
        '<NamedLayer>' +\
            '<Name>%s</Name>' +\
            '<UserStyle>' +\
                '<Name>%s</Name>' +\
                '<Title>%s</Title>' +\
                '%s' +\
            '</UserStyle>' +\
        '</NamedLayer>' +\
    '</StyledLayerDescriptor>'
point_symbolizer0 = '' +\
    '<PointSymbolizer>' +\
        '<Graphic>' +\
            '<Mark>' +\
                '<WellKnownName>circle</WellKnownName>' +\
                '<Fill>' +\
                    '<CssParameter name="fill">#FF0000</CssParameter>' +\
                '</Fill>' +\
            '</Mark>' +\
            '<Size>6</Size>' +\
        '</Graphic>' +\
    '</PointSymbolizer>'
line_symbolizer0 = '' +\
    '<LineSymbolizer>' +\
        '<Stroke>' +\
        '<CssParameter name="stroke">#000000</CssParameter>' +\
        '<CssParameter name="stroke-width">1</CssParameter>' +\
        '</Stroke>' +\
    '</LineSymbolizer>'
polygon_symbolizer0 = '' +\
    '<PolygonSymbolizer>' +\
        '<Fill>' +\
            '<CssParameter name="fill">#000080</CssParameter>' +\
            '<CssParameter name="fill-opacity">0.5</CssParameter>' +\
        '</Fill>' +\
        '<Stroke>' +\
            '<CssParameter name="stroke">#FFFFFF</CssParameter>' +\
            '<CssParameter name="stroke-width">2</CssParameter>' +\
        '</Stroke>' +\
    '</PolygonSymbolizer>'


def create_sld(xml_content):

    if "CIMDEGeographicFeatureLayer" not in xml_content:
        print '!!!!! XML file has no "CIMDEGeographicFeatureLayer" tage. !!!!!'
        return ['', 'XML file has no "CIMDEGeographicFeatureLayer" tage.']
    
    sld_root = xml_content['CIMDEGeographicFeatureLayer']

    sld_min_scale = sld_root['MaxScale']
    sld_max_scale = sld_root['MinScale']
    sld_title = sld_root['Name']
    sld_file_name = sld_root['FeatureTable']['DataConnection']['Dataset'].strip().lower()

    print "Creaing SLD file for %s" % sld_file_name

    # if sld_root['DisplayLabels'] == 'true':
    #     label_class = sld_root['LabelClasses']['CIMLabelClass']
    #     text_symbolizer = generate_text_symbolizer(label_class)
    
    # else:
    #     logging.info('SLD file <<%s>> does not display labels => "DisplayLabels is FALSE"' % sld_file_name)
    #     text_symbolizer = ''

    label_class = sld_root['LabelClasses']['CIMLabelClass']
    text_symbolizer = generate_text_symbolizer(label_class)
    symbolizer = sld_root['Symbolizer']

    # -------------------------------------------------------------------------------------------------------
    # #######################################################################################################
    # ##################################>       Multiple Rule        <#######################################
    # #######################################################################################################
    # -------------------------------------------------------------------------------------------------------
    if 'Groups' in symbolizer or 'Breaks' in symbolizer:
        

        if 'Groups' in symbolizer:
            groups = symbolizer['Groups']['CIMUniqueValueGroup']['Classes']['CIMUniqueValueClass']
            rule_filter_name = symbolizer['Fields']['String'].lower()
        elif 'Breaks' in symbolizer:
            groups = symbolizer['Breaks']['CIMClassBreak']
            rule_filter_name = symbolizer['Field'].lower()
            
            lower_bound = '0'
            if 'MinimumBreak' in symbolizer:
                lower_bound = symbolizer['MinimumBreak']
            
        if not isinstance(groups, list):
            tmp = []
            tmp.append(groups)
            groups = tmp

        rules = ''
        for ii in range(0, len(groups)):
            group = groups[ii]
            rule_symbolizer = []
            
            rule_filter_value = group['Label']
            if 'Groups' in symbolizer:
                rule_filter = '' +\
                    '<Filter xmlns="http://www.opengis.net/ogc">' +\
                        '<PropertyIsEqualTo>' +\
                            '<PropertyName>%s</PropertyName>' % rule_filter_name +\
                            '<Literal>%s</Literal>' % rule_filter_value +\
                        '</PropertyIsEqualTo>' +\
                    '</Filter>'
            
            elif 'Breaks' in symbolizer:
                upper_bound = group['UpperBound']
                if ii == range(0, len(groups))[0]:
                    rule_filter = '' +\
                        '<Filter xmlns="http://www.opengis.net/ogc">' +\
                            '<And>' +\
                                '<PropertyIsGreaterThanOrEqualTo>' +\
                                    '<PropertyName>%s</PropertyName>' % rule_filter_name +\
                                    '<Literal>%s</Literal>' % lower_bound +\
                                '</PropertyIsGreaterThanOrEqualTo>' +\
                                '<PropertyIsLessThan>' +\
                                    '<PropertyName>%s</PropertyName>' % rule_filter_name +\
                                    '<Literal>%s</Literal>' % upper_bound +\
                                '</PropertyIsLessThan>' +\
                            '</And>' +\
                        '</Filter>'
                
                elif ii == range(0, len(groups))[-1]:
                     rule_filter = '' +\
                        '<Filter xmlns="http://www.opengis.net/ogc">' +\
                            '<And>' +\
                                '<PropertyIsGreaterThanOrEqualTo>' +\
                                    '<PropertyName>%s</PropertyName>' % rule_filter_name +\
                                    '<Literal>%s</Literal>' % lower_bound +\
                                '</PropertyIsGreaterThanOrEqualTo>' +\
                                '<PropertyIsLessThanOrEqualTo>' +\
                                    '<PropertyName>%s</PropertyName>' % rule_filter_name +\
                                    '<Literal>%s</Literal>' % upper_bound +\
                                '</PropertyIsLessThanOrEqualTo>' +\
                            '</And>' +\
                        '</Filter>'
                
                else:
                    rule_filter = '' +\
                        '<Filter xmlns="http://www.opengis.net/ogc">' +\
                            '<And>' +\
                                '<PropertyIsGreaterThanOrEqualTo>' +\
                                    '<PropertyName>%s</PropertyName>' % rule_filter_name +\
                                    '<Literal>%s</Literal>' % lower_bound +\
                                '</PropertyIsGreaterThanOrEqualTo>' +\
                                '<PropertyIsLessThan>' +\
                                    '<PropertyName>%s</PropertyName>' % rule_filter_name +\
                                    '<Literal>%s</Literal>' % upper_bound +\
                                '</PropertyIsLessThan>' +\
                            '</And>' +\
                        '</Filter>'

                lower_bound = upper_bound

            symbol_type = group['Symbol']['Symbol']['@xsi:type'].replace('typens:CIM', '').replace('Symbol', '').lower()
            
            symbol_layers = group['Symbol']['Symbol']['SymbolLayers']
            if not isinstance(symbol_layers['CIMSymbolLayer'], list):
                    tmp = []
                    tmp.append(symbol_layers['CIMSymbolLayer'])
                    symbol_layers['CIMSymbolLayer'] = tmp

            min_scale_tag = '<MinScaleDenominator>%s</MinScaleDenominator>' % sld_min_scale
            max_scale_tag = '<MaxScaleDenominator>%s</MaxScaleDenominator>' % sld_max_scale

            # ================================================================================>
            # ================================================================================>     Point Symbolizer
            # ================================================================================>
            if 'point' in symbol_type:

                if ii == 0:
                    rules += '' +\
                        '<Rule>' +\
                            '<Name></Name>' +\
                            min_scale_tag + max_scale_tag + point_symbolizer0 + text_symbolizer + \
                        '</Rule>'

                for symbol_layer in symbol_layers['CIMSymbolLayer']:
                    sub_symbol_type = symbol_layer['@xsi:type']
                    
                    if 'PictureMarker' in sub_symbol_type:
                        marker_name = '%s_%s' % (sld_file_name, ii)
                        _point_symbolizer = '' +\
                            '<PointSymbolizer>' +\
                                '<Graphic>%s</Graphic>' % manage_picture_marker(marker_name, symbol_layer)+\
                            '</PointSymbolizer>'
                        rule_symbolizer.append(_point_symbolizer)
                    
                    elif 'CharacterMarker' in sub_symbol_type:
                        _point_symbolizer = '' +\
                            '<PointSymbolizer>%s' % manage_character_marker(symbol_layer)+\
                            '</PointSymbolizer>'
                        rule_symbolizer.append(_point_symbolizer)

                    elif 'SimpleMarker' in sub_symbol_type:
                        _point_symbolizer = '' +\
                            '<PointSymbolizer>%s' % manage_simple_marker(symbol_layer) +\
                            '</PointSymbolizer>'
                        rule_symbolizer.append(_point_symbolizer)
                    
                    # [ignored part]
                    elif 'VectorMarker' in sub_symbol_type:
                        _point_symbolizer = point_symbolizer0
                        rule_symbolizer.append(_point_symbolizer)
                        
                    else:
                        raise Exception("\n\nCreating Point Symbolizer => Unhandled Type <<%s>>\n\n" % sub_symbol_type)
                
                rule_symbolizer = rule_symbolizer[::-1]
                rule_symbolizer.insert(0, max_scale_tag)
                rule_symbolizer.insert(0, min_scale_tag)
                rule_symbolizer.append(text_symbolizer)


            # ================================================================================>
            # ================================================================================>     Line Symbolizer
            # ================================================================================>
            elif 'line' in symbol_type:

                if ii == 0:
                    rules += '' +\
                        '<Rule>' +\
                            '<Name></Name>' +\
                            min_scale_tag + max_scale_tag + line_symbolizer0 + text_symbolizer + \
                        '</Rule>'

                for symbol_layer in symbol_layers['CIMSymbolLayer']:
                    sub_symbol_type = symbol_layer['@xsi:type']
                    
                    if 'PlacedPoint' in sub_symbol_type:
                        _line_symbolizer = '' +\
                            '<LineSymbolizer>' +\
                                '<Stroke>%s</Stroke>' % manage_placed_point_layer(symbol_layer) +\
                            '</LineSymbolizer>'
                        rule_symbolizer.append(_line_symbolizer)

                    elif 'FilledStroke' in sub_symbol_type:
                        filled_stroke_part = manage_filled_stroke_layer(symbol_layer)
                        _line_symbolizer = '' +\
                            '<LineSymbolizer>' +\
                                '<Stroke>%s</Stroke>%s' % (filled_stroke_part['result_stk'], filled_stroke_part['result_pdc']) +\
                            '</LineSymbolizer>'
                        rule_symbolizer.append(_line_symbolizer)

                    else:
                        raise Exception("\n\nCreating Line Symbolizer => Unhandled Type <<%s>>\n\n" % sub_symbol_type)
                
                rule_symbolizer = rule_symbolizer[::-1]
                rule_symbolizer.insert(0, max_scale_tag)
                rule_symbolizer.insert(0, min_scale_tag)
                rule_symbolizer.append(text_symbolizer)


            # ================================================================================>
            # ================================================================================>     Polygon Symbolizer
            # ================================================================================>
            elif 'polygon' in symbol_type:
                
                min_scale_tag = '<MinScaleDenominator>%s</MinScaleDenominator>' % sld_min_scale
                max_scale_tag = '<MaxScaleDenominator>%s</MaxScaleDenominator>' % sld_max_scale

                if ii == 0:
                    rules += '' +\
                        '<Rule>' +\
                            '<Name></Name>' +\
                            min_scale_tag + max_scale_tag + polygon_symbolizer0 + text_symbolizer + \
                        '</Rule>'
                
                for symbol_layer in symbol_layers['CIMSymbolLayer']:
                    sub_symbol_type = symbol_layer['@xsi:type'].replace('typens:CIM','')

                    if sub_symbol_type == 'FilledStroke':
                        filled_stroke_part = manage_filled_stroke_layer(symbol_layer)
                        polygon_stroke_pattern = '' +\
                            '<PolygonSymbolizer>' +\
                                '<Stroke>' +\
                                    '%s' % filled_stroke_part['result_stk'] +\
                                '</Stroke>' +\
                                '%s' % filled_stroke_part['result_pdc'] +\
                            '</PolygonSymbolizer>'
                        rule_symbolizer.append(polygon_stroke_pattern)

                    elif sub_symbol_type == 'Fill':
                        pattern = symbol_layer['Pattern']
                        pattern_type = pattern['@xsi:type']
                        
                        if 'SolidPattern' in pattern_type:
                            pattern_dict = pattern['Color']
                            polygon_fill_solid = generate_hex_code(pattern_dict)
                            polygon_fill_pattern = '' +\
                                '<PolygonSymbolizer>' +\
                                    '%s' % generate_fill_tag(polygon_fill_solid) +\
                                '</PolygonSymbolizer>'
                        
                        elif 'Hatch' in pattern_type:
                            pattern_size = pattern['Separation']
                            pattern_dict = pattern['LineSymbol']['SymbolLayers']
                            polygon_fill_hatch = manage_hatch_pattern_layer(pattern_dict)
                            polygon_fill_pattern = '' +\
                                '<PolygonSymbolizer>' +\
                                    '<Fill>' +\
                                        '<GraphicFill>' +\
                                            '<Graphic>%s' % polygon_fill_hatch +\
                                            '<Size>%s</Size>' % pattern_size +\
                                            '</Graphic>' +\
                                        '</GraphicFill>' +\
                                    '</Fill>' +\
                                '</PolygonSymbolizer>'

                        elif 'Marker' in pattern_type:
                            pattern_dict = pattern['Symbol']['SymbolLayers']
                            polygon_fill_marker = manage_graphic_marker(pattern_dict)
                            polygon_fill_pattern = '' +\
                                '<PolygonSymbolizer>' +\
                                    '<Fill>' + polygon_fill_marker + '</Fill>' +\
                                '</PolygonSymbolizer>'
                        
                        # [ignored part]
                        elif 'Gradient' in pattern_type:
                            polygon_fill_pattern = ''

                        # [ignored part]
                        elif 'Tiled' in pattern_type:
                            polygon_fill_pattern = ''


                        else:
                            raise Exception("\n\nCreating Polygon Symbolizer => Unhandled pattern <<%s>>\n\n" % pattern_type)

                        rule_symbolizer.append(polygon_fill_pattern)
                    
                    # [ignored part]
                    elif sub_symbol_type == 'PlacedPointSymbols':
                        rule_symbolizer.append('')
                  
                    else:
                        raise Exception("\n\nCreating Polygon Symbolizer => Unhandled Type <<%s>>\n\n" % sub_symbol_type)

                rule_symbolizer = rule_symbolizer[::-1]
                rule_symbolizer.insert(0, max_scale_tag)
                rule_symbolizer.insert(0, min_scale_tag)
                rule_symbolizer.append(text_symbolizer)  


            rules += '<Rule><Name>%s</Name>%s%s</Rule>' % (rule_filter_value, rule_filter, ''.join(rule_symbolizer))
        
        feature_type_style = '<FeatureTypeStyle>%s</FeatureTypeStyle>' % rules
        return [sld_file_name, tag_root % (sld_file_name, sld_file_name, sld_title, feature_type_style)]


    # -------------------------------------------------------------------------------------------------------
    # #######################################################################################################
    # ###################################>       Single Rule        <########################################
    # #######################################################################################################
    # -------------------------------------------------------------------------------------------------------
    else:
        feature_type_style = ''
        
        symbol_type = symbolizer['Symbol']['Symbol']['@xsi:type'].lower()
        symbol_layers = symbolizer['Symbol']['Symbol']['SymbolLayers']

        min_scale_tag = '<MinScaleDenominator>%s</MinScaleDenominator>' % sld_min_scale
        max_scale_tag = '<MaxScaleDenominator>%s</MaxScaleDenominator>' % sld_max_scale

        if not isinstance(symbol_layers['CIMSymbolLayer'], list):
            tmp = []
            tmp.append(symbol_layers['CIMSymbolLayer'])
            symbol_layers['CIMSymbolLayer'] = tmp

        # ================================================================================>
        # ================================================================================>     Point Symbolizer
        # ================================================================================>
        if 'point' in symbol_type:
            point_symbolizers = []
            
            for symbol_layer in symbol_layers['CIMSymbolLayer']:
                sub_symbol_type = symbol_layer['@xsi:type']
                if 'PictureMarker' in sub_symbol_type:
                    _point_symbolizer = '' +\
                        '<PointSymbolizer>' +\
                            '<Graphic>%s</Graphic>' % manage_picture_marker(sld_file_name, symbol_layer) +\
                        '</PointSymbolizer>'
                    point_symbolizers.append(_point_symbolizer)
                
                elif 'CharacterMarker' in sub_symbol_type:
                    _point_symbolizer = '' +\
                        '<PointSymbolizer>%s' % manage_character_marker(symbol_layer) +\
                        '</PointSymbolizer>'
                    point_symbolizers.append(_point_symbolizer)
                
                elif 'SimpleMarker' in sub_symbol_type:
                    _point_symbolizer = '' +\
                        '<PointSymbolizer>%s' % manage_simple_marker(symbol_layer) +\
                        '</PointSymbolizer>'
                    point_symbolizers.append(_point_symbolizer)

                else:
                    raise Exception("\n\nCreating Point Symbolizer => Unhandled Type <<%s>>\n\n" % sub_symbol_type)
            
            point_symbolizers = point_symbolizers[::-1]
            point_symbolizers.insert(0, max_scale_tag)
            point_symbolizers.insert(0, min_scale_tag)
            point_symbolizers.append(text_symbolizer)

            feature_type_style += '<FeatureTypeStyle><Rule><Name/>%s</Rule></FeatureTypeStyle>' % (''.join(point_symbolizers))
            return [sld_file_name, tag_root % (sld_file_name, sld_file_name, sld_title, feature_type_style)]

        
        # ================================================================================>
        # ================================================================================>     Line Symbolizer
        # ================================================================================>
        elif 'line' in symbol_type:
            line_symbolizers = []

            for symbol_layer in symbol_layers['CIMSymbolLayer']:
                sub_symbol_type = symbol_layer['@xsi:type']

                if 'PlacedPoint' in sub_symbol_type:
                    _line_symbolizer = '' +\
                        '<LineSymbolizer>' +\
                            '<Stroke>%s</Stroke>' % manage_placed_point_layer(symbol_layer) +\
                        '</LineSymbolizer>'
                    line_symbolizers.append(_line_symbolizer)

                elif 'FilledStroke' in sub_symbol_type:
                    filled_stroke_part = manage_filled_stroke_layer(symbol_layer)
                    _line_symbolizer = '' +\
                        '<LineSymbolizer>' +\
                            '<Stroke>%s</Stroke>%s' % (filled_stroke_part['result_stk'], filled_stroke_part['result_pdc']) +\
                        '</LineSymbolizer>'
                    line_symbolizers.append(_line_symbolizer)

                else:
                    raise Exception("\n\nCreating Line Symbolizer => Unhandled Type <<%s>>\n\n" % sub_symbol_type)
            
            line_symbolizers = line_symbolizers[::-1]
            line_symbolizers.insert(0, max_scale_tag)
            line_symbolizers.insert(0, min_scale_tag)
            line_symbolizers.append(text_symbolizer)

            feature_type_style += '<FeatureTypeStyle><Rule><Name/>%s</Rule></FeatureTypeStyle>' % (''.join(line_symbolizers))
            return [sld_file_name, tag_root % (sld_file_name, sld_file_name, sld_title, feature_type_style)]

        
        # ================================================================================>
        # ================================================================================>     Polygon Symbolizer
        # ================================================================================>
        elif 'polygon' in symbol_type:
            polygon_symbolizers = []
            
            for symbol_layer in symbol_layers['CIMSymbolLayer']:
                sub_symbol_type = symbol_layer['@xsi:type'].replace('typens:CIM','')

                if sub_symbol_type == 'FilledStroke':
                    filled_stroke_part = manage_filled_stroke_layer(symbol_layer)
                    polygon_stroke_pattern = '' +\
                        '<PolygonSymbolizer>' +\
                            '<Stroke>' +\
                                '%s' % filled_stroke_part['result_stk'] +\
                            '</Stroke>' +\
                            '%s' % filled_stroke_part['result_pdc'] +\
                        '</PolygonSymbolizer>'
                    polygon_symbolizers.append(polygon_stroke_pattern)

                elif sub_symbol_type == 'Fill':
                    pattern = symbol_layer['Pattern']
                    pattern_type = pattern['@xsi:type']
                    
                    if 'SolidPattern' in pattern_type:
                        pattern_dict = pattern['Color']
                        polygon_fill_solid = generate_hex_code(pattern_dict)
                        polygon_fill_pattern = '' +\
                            '<PolygonSymbolizer>' +\
                                '%s' % generate_fill_tag(polygon_fill_solid) +\
                            '</PolygonSymbolizer>'
                    
                    elif 'Hatch' in pattern_type:
                        pattern_size = pattern['Separation']
                        pattern_dict = pattern['LineSymbol']['SymbolLayers']
                        polygon_fill_hatch = manage_hatch_pattern_layer(pattern_dict)
                        polygon_fill_pattern = '' +\
                            '<PolygonSymbolizer>' +\
                                '<Fill>' +\
                                    '<GraphicFill>' +\
                                        '<Graphic>%s' % polygon_fill_hatch +\
                                        '<Size>%s</Size>' % pattern_size +\
                                        '</Graphic>' +\
                                    '</GraphicFill>' +\
                                '</Fill>' +\
                            '</PolygonSymbolizer>'

                    elif 'Marker' in pattern_type:
                        pattern_dict = pattern['Symbol']['SymbolLayers']
                        polygon_fill_marker = manage_graphic_marker(pattern_dict)
                        polygon_fill_pattern = '' +\
                            '<PolygonSymbolizer>' +\
                                '<Fill>' + polygon_fill_marker + '</Fill>' +\
                            '</PolygonSymbolizer>'

                    # [ignored part]
                    elif 'Gradient' in pattern_type:
                        # pattern_dict = pattern['Symbol']['SymbolLayers']
                        # polygon_fill_marker = manage_gradient_pattern_layer(pattern_dict)
                        polygon_fill_pattern = ''

                    # [ignored part]
                    elif 'Tiled' in pattern_type:
                        polygon_fill_pattern = ''
                    
                    else:
                        raise Exception("\n\nCreating Polygon Symbolizer => Unhandled pattern <<%s>>\n\n" % pattern_type)

                    polygon_symbolizers.append(polygon_fill_pattern)
                
                # [ignored part]
                elif sub_symbol_type == 'PlacedPointSymbols':
                    polygon_symbolizers.append('')

                else:
                    raise Exception("\n\nCreating Polygon Symbolizer => Unhandled Type <<%s>>\n\n" % sub_symbol_type)
            
            polygon_symbolizers = polygon_symbolizers[::-1]
            polygon_symbolizers.insert(0, max_scale_tag)
            polygon_symbolizers.insert(0, min_scale_tag)
            polygon_symbolizers.append(text_symbolizer)

            feature_type_style += '<FeatureTypeStyle><Rule><Name/>%s</Rule></FeatureTypeStyle>' % (''.join(polygon_symbolizers))
            return [sld_file_name, tag_root % (sld_file_name, sld_file_name, sld_title, feature_type_style)]

            
if __name__ == "__main__":
    
    msd_full_path = r'C:\Users\Naghshara\Desktop\mxd_to_sld\msd\ioptc.msd'
    wrm_content_dir = extract_wrm(msd_full_path)
    if not wrm_content_dir:
        raise Exception("Cannot decompress <<wrm>> file.")

    msd_dir, project_name = os.path.split(msd_full_path)

    project_root_dir = wrm_content_dir
    
    generated_sld_dir = wrm_content_dir + "\\sld_files"
    if not is_exist(generated_sld_dir):
        os.makedirs(generated_sld_dir)
    
    generated_img_dir = wrm_content_dir + "\\img_files"
    if not is_exist(generated_img_dir):
        os.makedirs(generated_img_dir)
        tmp = codecs.open(os.path.abspath(os.path.join(msd_dir, os.pardir)) + "\\tmp.txt", "w", "utf-8")
        tmp.write(generated_img_dir)
        tmp.close()

    wrm_content_dir += "\\layers"
    for xml_file in os.listdir(wrm_content_dir):
        
        logging.info('\n')
        logging.info(datetime.now())
        logging.info('Creating SLD for file <<%s>> .... ' % xml_file)

        if xml_file.endswith(".xml"):
            xml_style_dir = wrm_content_dir + "\\" + xml_file
            mxd_style_dict = parse_xml(xml_style_dir)
            sld_name, sld_content = create_sld(mxd_style_dict)

            if sld_name and sld_content:
                if 'hormozgan.dbo.' in sld_name:
                    sld_name = sld_name.replace('hormozgan.dbo.','')
                results = codecs.open(generated_sld_dir + "\\%s.sld" % sld_name, "w", "utf-8")
                results.write(sld_content)
                results.close()

                logging.info('%s.sld file was created successfully.' % xml_file)

            else:
                logging.error('Error in creating SLD fild => <<%s>> .... ' % xml_file)
                logging.error(sld_content)

        else:
            continue
    
    logging.info('\n')
    logging.info('Process Completed Successfully.')
    logging.info('SLD Files -> %s' % generated_sld_dir)
    logging.info('IMG Files -> %s' % generated_img_dir)
    
    print '\n'
    print '--------------------------------------------------------------------'
    print 'Process Completed Successfully.'
    print '--------------------------------------------------------------------'
    print 'SLD Files ->', generated_sld_dir
    print 'IMG Files ->', generated_img_dir
    print 'You can remove ./layers' 
    print '--------------------------------------------------------------------'
    print '\n'
    
    if is_exist(project_root_dir):
        purge_project(project_root_dir)