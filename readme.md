# Description
This is an app for an experiment at the Biomedical Microtechnology lab of the University of Freiburg. 
It was developed by Julian Webb.
It uses the Hasomed P24 Science Stimulator to stimulate on the backside of the knee using surface electrodes to evoke sensations.
The participant is asked to input their sensations by the application and these are stored.

# Installation
* [The ScienceMode4_python_wrapper](https://github.com/ScienceMode/ScienceMode4_python_wrapper) must be installed in the project's root directory.  
* [gettext (GNU Project)](https://www.gnu.org/software/gettext/) must be installed for localization
* Install the packages from the `rrequirements.txt` file into your virtual environment
* Then, the app can be run from your virtual environment

# Comments
* You can find a lot of documentation for native functions of the Stimulator here:
`ScienceMode4_python_wrapper\.eggs\cffi-1.17.1-py3.12-win-amd64.egg\cffi\api.py`

# Adding new Strings
The app uses the gettext module for localization (translation to German and English).  
* When adding new strings, they must be added to the localization. Wrap the strings in the gettext 
function like this ``_("New String")`` in the code.
* To update the ``messages.pot`` file, run the following command from the project root (EvokedSensations folder): 
``xgettext -d messages -o locales/messages.pot widgets/*.py --from-code UTF-8``
* Update .po files using msgmerge (German, English):
`msgmerge -U locales/de/LC_MESSAGES/messages.po locales/messages.pot; msgmerge -U locales/en/LC_MESSAGES/messages.po locales/messages.pot`
* Translate the new strings in the ``locales/de/LC_MESSAGES/messages.po`` file
* To update the machine-readable ``messages.mo`` files, run: 
``msgfmt locales/de/LC_MESSAGES/messages.po -o locales/de/LC_MESSAGES/messages.mo; msgfmt locales/en/LC_MESSAGES/messages.po -o locales/en/LC_MESSAGES/messages.mo``

For more information, check this tutorial on lokalise.com: https://lokalise.com/blog/translating-apps-with-gettext-comprehensive-tutorial/