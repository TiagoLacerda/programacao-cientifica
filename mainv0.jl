using JSON
using LinearAlgebra
using SparseArrays

# Gera o sistema de equações sem usar connect

function loadJSON(filename)
    open(filename, "r") do file
        data = JSON.parse(file)
        return data
    end
end

function saveJSON(filename, data)
    open(filename, "w") do j
        write(j, JSON.json(data))
    end
end


function block(h, k)  # h ~ dx, k ~ dy, MID LFT RGT BOT TOP
    c1 = 2.0 * ((h / k) ^ 2.0 + 1)
    c2 = -(h / k) ^ 2.0
    c3 = c2
    c4 = -1.0
    c5 = c4

    return c1, c2, c3, c4, c5
end


function numerical(n, h, k, I, J, T)  # h ~ dx, k ~ dy
    c1, c2, c3, c4, c5 = block(h, k)

    A = spzeros(Float64, n, n)
    b = zeros(Float64, n)

    map = Dict()

    # I é um vetor com o índice da linha  correspondente à particula
    # J é um vetor com o índice da coluna correspondente à particula
    # T é um vetor com a temperatura correspondente à particula (null se não conhecida)

    for index = 1:n
        i = I[index]
        j = J[index]
        map[(i, j)] = index
    end

    for index = 1:n
        i = I[index]
        j = J[index]
        t = T[index]

        if isnothing(t)
            # Interno (necessariamente tem todos os 4 vizinhos)
            # c1 * T[i,j] - T[i,j - 1] - T[i,j + 1] - T[i - 1,j] - T[i + 1,j] = 0
            A[index, index] =           c1  # MID
            A[index, map[(i, j - 1)]] = c2  # LFT
            A[index, map[(i, j + 1)]] = c3  # RGT
            A[index, map[(i - 1, j)]] = c4  # BOT
            A[index, map[(i + 1, j)]] = c5  # TOP
            b[index] = 0.0
        else
            # Externo (contorno)
            A[index, index] = 1.0
            b[index] = t
        end
    end

    result = A\b
    return result
end


function main(infilename, outfilename)
    data = loadJSON(infilename)

    n = data["n"]
    h = data["dx"]
    k = data["dy"]
    I = data["i"]
    J = data["j"]
    T = data["t"]
    
    result = numerical(n, h, k, I, J, T)

    data["t"] = result
    data["mint"] = minimum(data["t"])
    data["maxt"] = maximum(data["t"])
    saveJSON(outfilename, data)
end


if (length(ARGS) == 2)
    main(ARGS[1], ARGS[2])
end
