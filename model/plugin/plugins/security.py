#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import logging
import os

from lxml import etree

from smartcard.util import toHexString, toASCIIString, PACK

from model.plugin.plugins.base_plugin import base_plugin
from constant.apdu import FILE_ID, CODING_P1_SELECT, CODING_P2_SELECT
from utility.fcp import TLV_TAG, get_data_length, get_record_count, search_fcp_content
from utility.convert import BCDtoDecimalString


DEF_SECURITY_XML_FOLDER = "security_cache"


class security(base_plugin):
    def __init__(self):
        self.__logging = logging.getLogger(os.path.basename(__file__))

    def summary(self):
        return "Store the PIN/ADM code to xml file for future verify automatically."

    def help(self):
        return ("Usage:\n"
                " security pin=xxxxxxxx adm=xxxxxxxxxxxxxxxx\n"
                "  - pin: 4 ~ 8 digits\n"
                "  - adm: 16 HEX digits\n"
                "\n"
                "Example:\n"
                "  security pin=1234 adm=5555555555555555\n"
                "\n"
                " PS. The xml file name is base on ICCID of USIM.")

    @property
    def auto_execute(self):
        return False

    def execute(self, arg_connection, arg_parameter=None):
        self.__logging.debug("execute()")

        if not os.path.exists(DEF_SECURITY_XML_FOLDER):
            os.makedirs(DEF_SECURITY_XML_FOLDER)

        ret_content = "Unexpected error!!"

        adm_code = None
        pin_code = None
        key_list = arg_parameter.split(" ")
        for key in key_list:
            value = key.split("=")
            if value[0] == "adm":
                adm_code = value[1]
            elif value[0] == "pin":
                pin_code = value[1]

        if (adm_code == None or
            pin_code == None or
            len(adm_code) != 16 or
                len(pin_code) < 4 or len(pin_code) > 8):
            ret_content = "Invalid PIN/ADM code, operation terminated!!"
        else:
            # select MF
            response, sw1, sw2 = arg_connection.select(
                FILE_ID.MF.value, arg_p2_coding=CODING_P2_SELECT.SEL_NO_DATA_RETURN.value)

            if sw1 == 0x90:
                # select EF_ICCID
                response, sw1, sw2 = arg_connection.select(
                    FILE_ID.ICCID.value, arg_p1_coding=CODING_P1_SELECT.SEL_FROM_MF.value)

                if sw1 == 0x90:
                    data_length = get_data_length(response)
                    response, sw1, sw2 = arg_connection.read_binary(
                        data_length)

                    iccid = BCDtoDecimalString(response)

                    try:
                        security_node = etree.Element("security")
                        adm_node = etree.SubElement(security_node, "adm")
                        adm_node.text = adm_code
                        pin_node = etree.SubElement(security_node, "pin")
                        pin_node.text = pin_code
                        xmltree = etree.ElementTree(security_node)
                        xmltree.write(DEF_SECURITY_XML_FOLDER + os.sep + iccid + ".xml", pretty_print=True,
                                      xml_declaration=True, encoding='utf-8')
                        ret_content = "The " + iccid + ".xml file stored success."
                    except:
                        ret_content = "Can't store " + iccid + ".xml file, operation terminated!"

        return ret_content
