#!/usr/bin/env python
# -*- coding: utf-8 -*-
#title           :menu.py
#description     :This program displays an interactive menu on CLI
#author          :
#date            :
#version         :0.1
#usage           :python menu.py
#notes           :
#python_version  :3.10
#reference       :https://www.bggofurther.com/2015/01/create-an-interactive-command-line-menu-using-python/
#=======================================================================

# Import the modules needed to run the script.
import sys, os
from taxgen import TaxGen, DataSource

# Main definition - constants
menu_actions  = {}
tax_gen = TaxGen()

# =======================
#     MENUS FUNCTIONS
# =======================

# Main menu
def main_menu():
    os.system('clear')

    print ( "Welcome,\n" )
    print ( "Please choose the menu you want to start:" )
    print ( "1. Load Coinbase fills" )
    print ( "2. Calculate Tax" )
    print ( "\n0. Quit" )
    choice = input(" >>  ")
    exec_menu(choice)

    return

# Execute menu
def exec_menu(choice):
    # os.system('clear')
    ch = choice.lower()
    if ch == '':
        menu_actions['main_menu']()
    else:
        try:
            menu_actions[ch]()
        except KeyError:
            print ( "Invalid selection, please try again.\n" )
            menu_actions['main_menu']()
    return

def exec_load_menu(choice):
    ch = choice
    if ch == '' or ch == 'back':
        menu_actions['main_menu']()
        return
    elif ch == 'view':
        tax_gen.print_files()
    elif ch == "stats":
        tax_gen.print_stats()
    else:
        tax_gen.load(DataSource.Coinbase, choice)
    menu_actions['load']()

# Menu 1
def load():
    print ( "Load fills transactions from Coinbase !\n" )
    print ( "Type csv path to load. ie: /home/coinbase_2021.csv" )
    print ( "Type view for list of loaded files." )
    print ( "Type stats for statistic in of current source" )
    print ( "Type back to go back" )
    choice = input(" >>  ")
    exec_load_menu(choice)
    return


# Menu 2
def tax_report():
    print ( "Exporting tax based on inputed transactions" )
    tax_gen.gen_tax_reports()
    print ( "hit any key to go back" )
    choice = input(" >>  ")
    return

# Back to main menu
def back():
    menu_actions['main_menu']()

# Exit program
def exit():
    sys.exit()

# =======================
#    MENUS DEFINITIONS
# =======================

# Menu definition
menu_actions = {
    'main_menu': main_menu,
    'load': load,
    '1': load,
    '2': tax_report,
    '9': back,
    '0': exit,
}

# =======================
#      MAIN PROGRAM
# =======================

# Main Program
if __name__ == "__main__":
    # Launch main menu
    main_menu()
