.PHONY: clean prepare drc gerbers schematic pdfs drc_carrier gerbers_carrier schematic_carrier pdfs_carrier drc_m2 gerbers_m2 schematic_m2 pdfs_m2
.ONESHELL:

# Install dependencies (for local development)
prepare:
	pip3 install --quiet --break-system-packages kikit

# Clean all generated files
clean:
	rm -rf hardware/production hardware/pdfs

# Blackpants board targets
drc:
	mkdir -p hardware/production
	kikit drc run ./hardware/blackpants.kicad_pcb

gerbers:
	mkdir -p hardware/production
	kikit fab jlcpcb --assembly --schematic hardware/blackpants.kicad_sch hardware/blackpants.kicad_pcb hardware/production

schematic:
	mkdir -p hardware/pdfs
	kicad-cli sch export pdf --output hardware/pdfs/schematic.pdf hardware/blackpants.kicad_sch

pdfs:
	mkdir -p hardware/pdfs
	kicad-cli pcb export pdf --mode-separate --output hardware/pdfs hardware/blackpants.kicad_pcb -l "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,Edge.Cuts,F.Fab,B.Fab"

# Backward compatibility aliases for old target names
drc_carrier: drc
gerbers_carrier: gerbers
schematic_carrier: schematic
pdfs_carrier: pdfs
drc_m2: drc
gerbers_m2: gerbers
schematic_m2: schematic
pdfs_m2: pdfs
