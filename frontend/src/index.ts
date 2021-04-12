import { io, Socket } from "socket.io-client"


function getSocket(): Socket {
    const socket = io()
    const updateTiles = (jsonGameState: string): void => {
        const gameState = JSON.parse(jsonGameState)
        const grid = <HTMLDivElement>document.getElementById("gameGrid")
        const children = grid.children

        for (let i = 0; i < children.length; i++) {
            const child = <HTMLDivElement>children.item(i)
            const row = parseInt(child.getAttribute("row") ?? "")
            const col = parseInt(child.getAttribute("col") ?? "")

            child.innerText = gameState[row][col]
        }
    }

    socket.on("board", updateTiles)
    socket.on("open", updateTiles)

    return socket
}

function setupTiles(socket: Socket): void {
    const openTile = (row: number, col: number): void => {
        socket.emit("open", row, col)
    }

    const createMinesweeperTile = (i: number, j: number): HTMLDivElement => {
        const newDiv = <HTMLDivElement>document.createElement("div")
        newDiv.setAttribute("class", "cell")
        newDiv.setAttribute("row", i.toString())
        newDiv.setAttribute("col", j.toString())
        newDiv.onclick = function() {
            openTile(i, j)
        }

        return newDiv
    }

    window.onload = () => {
        const rows = 10
        const cols = 10
        const grid = document.getElementById("gameGrid")

        for (let i = 0; i < rows; i++) {
            for (let j = 0; j < cols; j++) {
                const newDiv = createMinesweeperTile(i, j)
                grid?.appendChild(newDiv)
            }
        }
    }
}

function main(): void {
    const socket = getSocket()
    setupTiles(socket)
    socket.emit("board") // Request the current state of the game to render on the page
}

main()