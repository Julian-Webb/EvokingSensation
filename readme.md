# Comments
* You can find a lot of documentation for native functions of the Stimulator here:
`ScienceMode4_python_wrapper\.eggs\cffi-1.17.1-py3.12-win-amd64.egg\cffi\api.py`

# Adding new Strings

* When adding new strings, they must be added to the localization (translation to German). Wrap the strings in the gettext 
function like this ``_("New String")`` in the code.
* To update the ``messages.pot`` file, run the following command from the project root (EvokedSensations folder): 
``xgettext -d messages -o locales/messages.pot widgets/*.py --from-code UTF-8``
* Update .po files using msgmerge (German, English):
`msgmerge -U locales/de/LC_MESSAGES/messages.po locales/messages.pot; msgmerge -U locales/en/LC_MESSAGES/messages.po locales/messages.pot`
* Translate the new strings in the ``locales/de/LC_MESSAGES/messages.po`` file
* To update the machine-readable ``messages.mo`` files, run: 
``msgfmt locales/de/LC_MESSAGES/messages.po -o locales/de/LC_MESSAGES/messages.mo; msgfmt locales/en/LC_MESSAGES/messages.po -o locales/en/LC_MESSAGES/messages.mo``

For more information, check this tutorial on lokalise.com: https://lokalise.com/blog/translating-apps-with-gettext-comprehensive-tutorial/