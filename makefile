.PHONY: compile sync update

compile:
	pip-compile requirements.in

sync:
	pip-sync requirements.txt

update:
	pip-compile --upgrade requirements.in
	pip-sync requirements.txt

# Upon initial setup:
# make sync

# Upon adding new packages:
# echo "package-name" >> requirements.in
# make compile
# make sync

# Upon updating packages:
# make update

# Note to self: 
# Typically, don't update packages unless necessary, this is not Arch Linux.