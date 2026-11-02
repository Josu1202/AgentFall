# Subir Agentfall a GitHub

La carpeta que contenga `main.py`, `README.md`, `.gitignore` y `.github/` debe
ser la raiz del repositorio. Si usas el ZIP, descomprimelo primero. El ZIP es
el medio de entrega; sube sus archivos extraidos para que GitHub muestre el
codigo y encuentre las pruebas automaticas.

## Con Git desde VS Code o PowerShell

1. Instala [Git](https://git-scm.com/downloads) si no lo tienes y comprueba
   `git --version` en una terminal nueva.
2. Crea un repositorio vacio en [GitHub](https://github.com/new). Puedes llamarlo
   `agentfall` y elegir su visibilidad. Durante la creacion deja desmarcadas las
   opciones que anaden README, `.gitignore` o licencia: este proyecto ya lleva
   los archivos necesarios para su primer commit.
3. Abre una terminal dentro de la carpeta extraida, donde esta `main.py`.
4. Ejecuta cada comando por separado:

```powershell
git init -b main
git add .
git status
git commit -m "Initial commit: Agentfall"
```

`git status` debe incluir `.github/workflows/tests.yml` y los archivos del juego.
Las carpetas `.venv`, `.venv313` y `__pycache__` quedan excluidas automaticamente.
Si Git solicita tu nombre o correo, configura los que quieras asociar al commit
y repite `git commit`:

```powershell
git config user.name "TU_NOMBRE"
git config user.email "TU_CORREO_DE_GITHUB"
```

5. Copia la URL HTTPS que GitHub muestra para tu repositorio. En los comandos
   siguientes, sustituye `TU_USUARIO` por tu usuario real y `agentfall` por el
   nombre que elegiste:

```powershell
git remote add origin https://github.com/TU_USUARIO/agentfall.git
git push -u origin main
```

Completa el inicio de sesion que solicite Git. Para actualizaciones posteriores:

```powershell
git add .
git commit -m "Describe el cambio realizado"
git push
```

## Con GitHub Desktop

1. En [GitHub Desktop](https://desktop.github.com/), usa **File > Add local
   repository** y selecciona la carpeta que contiene `main.py`.
2. Si todavia no tiene repositorio Git, utiliza la opcion para crearlo en esa
   misma carpeta. Conserva el `.gitignore` incluido.
3. Revisa los archivos, crea el primer commit si hace falta y pulsa
   **Publish repository**. Elige el nombre y la visibilidad.

## Comprobaciones automaticas

Abre la pestana **Actions** del repositorio despues de subirlo. El workflow
**Tests** esta configurado para Python 3.12 y 3.13 en Windows y Linux. Instala
pygame, comprueba dependencias, ejecuta los tests y arranca 180 fotogramas sin
pantalla. Tambien se puede lanzar con **Run workflow**.

El resultado de esas ejecuciones se vera en GitHub una vez publicado el codigo.
Puedes ejecutar los mismos comandos localmente; estan en `README.md`.

Referencias: [subir codigo local](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github)
y [pruebas de Python en Actions](https://docs.github.com/en/actions/tutorials/build-and-test-code/python).
