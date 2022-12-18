import { io, Socket } from "socket.io-client"
import { Board, createBoard } from "./Game"

function parseGameJSON(jsonGameState: string): Array<Array<string>> {
    return <Array<Array<string>>>JSON.parse(jsonGameState)
}

function getActiveGame(socket: Socket) {
    if (localStorage.getItem("loggedInUser")) {
        if (document.getElementById("logout")?.style.visibility !== "visible") {

            document.getElementById("logout")!.style.visibility = "visible"
            document.getElementById("loginmsg")!.innerHTML = localStorage.getItem("loggedInUser")!
        }
        socket.emit("resume", localStorage.getItem("loggedInUser"))
    } else {
        if (localStorage.getItem("activeGame")) {
            socket.emit("load", localStorage.getItem("activeGame"));
        } else {
            socket.emit("board")
        }
    }
    //TODO:if user is logged in, load their game stored in DB
}


function setupSocket(socket: Socket): void {
    let board: Board

    const resetButton = <HTMLButtonElement>document.getElementById("resetGame")
    resetButton.onclick = () => {
        localStorage.setItem("activeGame", "") //this can be either here or in board switch case
        socket.emit("reset")
    }

    const login = <HTMLInputElement>document.getElementById("login")
    login.onclick = () => {
        socket.emit("login", (document.getElementById("user") as HTMLInputElement).value, (document.getElementById("pass") as HTMLInputElement).value)
    }

    const register = <HTMLInputElement>document.getElementById("register")
    register.onclick = () => {
        socket.emit("register", (document.getElementById("user") as HTMLInputElement).value, (document.getElementById("pass") as HTMLInputElement).value)
    }

    const logout = <HTMLInputElement>document.getElementById("logout")
    logout.onclick = () => {
        localStorage.setItem("loggedInUser", "")
        loginmsg.innerHTML = ""
        logout.style.visibility = "hidden"
        socket.emit("logout")
    }

    const firstTurnButton = <HTMLButtonElement>document.getElementById("first")
    firstTurnButton.onclick = () => {
        socket.emit("step", "first")
    }

    const prevButton = <HTMLButtonElement>document.getElementById("prev")
    prevButton.onclick = () => {
        socket.emit("step", -1)
    }

    const lastTurnButton = <HTMLButtonElement>document.getElementById("last")
    lastTurnButton.onclick = () => {
        socket.emit("step", "last")
    }

    const nextButton = <HTMLButtonElement>document.getElementById("next")
    nextButton.onclick = () => {
        socket.emit("step", 1)
    }
    

    const gameOver = <HTMLElement>document.getElementById("gameOver")

    const loginmsg = <HTMLElement>document.getElementById("loginmsg")


    function openTile(row: number, col: number): void {
        socket.emit("open", row, col)
    }

    //function login() {
        
    //}

    socket.onAny((eventName: string, ...args: string[]) => {
        switch (eventName) {
            case "board": {
                if (gameOver.innerHTML) {
                    gameOver.innerHTML = "";
                }
                const gameState = parseGameJSON(args[0])
                const rows = gameState.length
                const cols = gameState[0].length
                board = createBoard(rows, cols)

                for (const [[row, col], tile] of board) {
                    tile.value = gameState[row][col]
                    // add functionality for flagging tiles
                    tile.setOnClick(() => openTile(row, col))
                }

                break
            }
            
            case "open": {
                const gameState = parseGameJSON(args[0])
                //store game in localStorage only if guest, otherwise server will store
                //for registered user
                localStorage.setItem("activeGame", args[0])
                for (const [[row, col], tile] of board) {
                    tile.value = gameState[row][col]
                }
                break
            }
            
            case "lose": {
                gameOver.innerHTML = "Game Over"
                const gameState = parseGameJSON(args[0])
                localStorage.setItem("activeGame", "")
                //delete game in localStorage if guest
                for (const [[row, col], tile] of board) {
                    tile.value = gameState[row][col]
                    tile.setOnClick(() => null)
                }
                firstTurnButton.style.visibility = "visible"
                prevButton.style.visibility = "visible"
                nextButton.style.visibility = "visible"
                lastTurnButton.style.visibility = "visible"
                break
            }

            case "win": {
                gameOver.innerHTML = "You win!"
                const gameState = parseGameJSON(args[0])
                localStorage.setItem("activeGame", "")
                for (const [[row, col], tile] of board) {
                    tile.value = gameState[row][col]
                    tile.setOnClick(() => null)
                }
                socket.emit("end")
                firstTurnButton.style.visibility = "visible"
                prevButton.style.visibility = "visible"
                nextButton.style.visibility = "visible"
                lastTurnButton.style.visibility = "visible"
                break
            }

            case "loginfail": {
                loginmsg.innerHTML = "Login failed"
                break
            }

            case "loginsuccess": {
                loginmsg.innerHTML = args[0]
                logout.style.visibility = "visible"
                localStorage.setItem("loggedInUser", args[0])
                //console.log("success")
                //console.log(args[0])
                getActiveGame(socket)
                break
            }

            case "registerfail": {
                loginmsg.innerHTML = "Register failed"
                break
            }

            case "registersuccess": {
                loginmsg.innerHTML = "Register successful"
                break
            }

            default: {
                throw `Unknown event ${eventName}`
            }
        }
    })
}

function main(): void {
    const socket = io()
    setupSocket(socket)
    getActiveGame(socket)
}

window.onload = main