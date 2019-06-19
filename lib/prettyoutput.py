"""
Colorama Functions - Part of SmtpRelaySpoof
"""

from colorama import Fore, Style
def output_ok(line):
    print(Fore.LIGHTRED_EX + Style.NORMAL + "[+]" + Style.RESET_ALL, line)


def output_good(line):
    print(Fore.GREEN + Style.BRIGHT + "[+]" + Style.RESET_ALL, line)


def output_indifferent(line):
    print(Fore.BLUE + Style.BRIGHT + "[*]" + Style.RESET_ALL, line)


def output_error(line):
    print(Fore.RED + Style.BRIGHT + "[-] !!! " + Style.NORMAL, line, Style.BRIGHT + "!!!" + Style.RESET_ALL)


def output_bad(line):
    print(Fore.RED + Style.BRIGHT + "[-]" + Style.RESET_ALL, line)


def output_info(line):
    print(Fore.LIGHTBLUE_EX + Style.NORMAL + "[*]" + Style.RESET_ALL, line)
