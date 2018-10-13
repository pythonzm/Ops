#!/usr/bin/python
# -*- coding: utf-8 -*-


import json
import sys
import commands


def get_mem_info():
    mem_data = []
    data = {}
    status, output = commands.getstatusoutput("dmidecode -t 17|awk '/(Manufacturer|Size|Serial Number)/'")

    output_list = output[1:].rstrip().split('\n\t')

    new_list = [output_list[i:i + 3] for i in range(0, len(output_list), 3)]

    for index, i in enumerate(new_list):
        size = i[0].split(':')[1].lstrip()
        if not size.startswith("No"):
            data['ram_volume'] = size
            data['ram_slot'] = index + 1
            data['ram_brand'] = i[1].split(':')[1].lstrip()
            data['ram_serial'] = i[2].split(':')[1].lstrip()
            mem_data.append(data)

    return mem_data


print(json.dumps({
    "changed": False,
    "ansible_facts": {
        "mem_info": get_mem_info(),
    }
}))

sys.exit(0)

