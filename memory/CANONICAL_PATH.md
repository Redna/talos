# Canonical Memory Path
All identity, state, and knowledge files MUST reside in `/app/memory/`. 
The root-level `/memory/` directory is a legacy mirror and is NOT tracked by Git.
Any writes to `/memory/` are transient and will be lost on restart.
Standard: `/app/memory/[file]`
