import re
from bs4 import BeautifulSoup
from urllib.request import urlopen


def find_device_info():
    with open(r'commands/nicinfo.sh.txt', 'r', encoding='utf-8') as f:
        result = []
        state = 0
        all_file = f.readlines()
        for i in all_file:
            if i.count('--\n'):
                state = 1
            if re.match('^NIC', i):
                state = 0
            elif state == 1:
                result.append(i.split())
        result.pop(0)
        result.pop()
        result_map = {}
        for i in result:
            result_map[' '.join(i[9:])] = i[2]
        return result_map


def find_driver_version(nic_info):
    pattern_driver = 'Driver: (.*?)\n'
    pattern_fv = 'Firmware Version: (.*?)\n'
    pattern_version = '  Version: (.*?)\n'

    return re.sub('\n', '', str(re.search(pattern_driver, nic_info).group(0)
                                + re.sub('  Version:', '', re.search(pattern_version, nic_info).group(0)))
                  + ", "
                  + re.sub('Firmware Version', 'FW', re.search(pattern_fv, nic_info).group(0)))


def find_bios_info():
    with open(r'commands/smbiosDump.txt', 'r', encoding='utf-8') as file:
        state = 0
        result = ''
        bios_dump = file.readlines()
        for i in bios_dump:
            if re.search('BIOS Info:(.*?)\n', i) is not None:
                state = 1
            if re.search('Date:(.*?)\n', i) is not None:
                state = 0
            elif state == 1:
                if re.search('Version:(.*?)\n', i) is not None:
                    result = re.sub('Version', 'BIOS Version', re.search('Version:(.*?)\n', i).group(0))
        for i in bios_dump:
            if re.search('System Info:(.*?)\n', i) is not None:
                state = 1
            if re.search('UUID:(.*?)\n', i) is not None:
                state = 0
            elif state == 1:
                if re.search('Product:(.*?)\n', i) is not None:
                    result += re.sub('\n', '', re.search('Product:(.*?)\n', i).group(0))
        return result


def find_esxi_info():
    result = ''
    with open(r'commands/vmware_-vl.txt', 'r', encoding='utf-8') as file:
        vmware = file.readlines()
        result += 'OS: ' + vmware[0] + vmware[1][17:]
    return re.sub('\n', '', result)


def find_version_in_site(url):
    global url_d
    resp = urlopen(url)
    re.sub(r'/', '', 'html_{}'.format(url) + '.txt')
    html = resp.read().decode('utf-8')
    soup = BeautifulSoup(str(html), 'html.parser')
    for i in soup.find_all('div', attrs={'class': 'result'}):
        for a in i.find_all('a', href=True):
            url_d = re.sub('../', 'https://www.vmware.com/resources/compatibility/', a['href'])
            break
        break
    resp_d = urlopen(url_d)
    html_d = resp_d.read().decode('utf-8')
    result = ''
    with open('thml_https.txt', 'w', encoding='utf-8') as file:
        file.write(str(html_d))
    with open('thml_https.txt', 'r', encoding='utf-8') as file:
        ent = file.readlines()
        for i in ent:
            if re.match('ESXi 6.0 U3,(.*?)\n', i):
                result = result + i
                break
    return re.sub(',', ', ', result)


def main():
    with open(r'commands/nicinfo.sh.txt', 'r', encoding='utf-8') as f:
        state = 0  # состояние, когда идет запись нужного участка == 1
        info = []
        str_info = ''
        table = ''
        s = f.readlines()
        for itr in s:
            if itr == 'NICInfo:\n':
                state = 1
            if re.match('Ring parameters', itr):
                info.append(str_info)
                state = 0
                str_info = ''
            elif state == 1:
                str_info = str_info + itr

        for i in s:
            table += i
            if re.match('NIC:(.*?)\n', i):
                table = re.sub("NIC:(.*?)\n", '', table)
                break

        device_map = find_device_info()

        for i in info:
            result_driver_version = find_driver_version(i)
            for key in device_map:
                if result_driver_version.count(device_map[key]) > 0:
                    device_map[key] = result_driver_version

        print(find_bios_info())
        print(find_esxi_info())
        print('\n' + table)
        devices = set()

        for key in device_map:
            if key.find('82580') != -1:
                devices.add('D2755')
            else:
                devices.add(re.sub('\)', '%29', re.sub('\(', '%28', re.sub(' ', '+', key))))
            print(key + ' -> ' + device_map[key])
        print('-------------------------------------------------------')
        print('VMWare Compatibility Matrix:')
        for i in devices:
            print(re.sub('%29', ')', re.sub('%28', '(', re.sub('\+', ' ', i))))
            print(find_version_in_site(
                r'https://www.vmware.com/resources/compatibility/vcl/result.php?search={}&searchCategory=all'.format(
                    i)))


main()
