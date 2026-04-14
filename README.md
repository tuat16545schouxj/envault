# envault

> A CLI tool for securely managing and syncing environment variables across local and remote dev environments.

---

## Installation

```bash
pip install envault
```

Or with [pipx](https://pypa.github.io/pipx/) (recommended):

```bash
pipx install envault
```

---

## Usage

Initialize a new vault in your project:

```bash
envault init
```

Add and encrypt an environment variable:

```bash
envault set DATABASE_URL "postgres://user:pass@localhost/mydb"
```

Sync variables to a remote environment:

```bash
envault push --env production
```

Pull variables on another machine:

```bash
envault pull --env production
```

Export variables to a local `.env` file:

```bash
envault export > .env
```

---

## How It Works

`envault` encrypts your environment variables using AES-256 and stores them in a versioned vault file. Vaults can be synced to a remote backend (S3, GitHub Gist, or a self-hosted server), allowing teams to share secrets securely without committing them to source control.

---

## License

This project is licensed under the [MIT License](LICENSE).