using JSON
using LinearAlgebra
using SparseArrays

# Gera o sistema de equações utilizando connect da forma vista em aula

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


function getBlock(h, k)  # h ~ dx, k ~ dy, Middle Left Right Bottom Top
    c1 = 2.0 * ((h / k) ^ 2.0 + 1)
    c2 = -(h / k) ^ 2.0
    c3 = c2
    c4 = -1.0
    c5 = c4

    return [c1, c2, c3, c4, c5]
end


function numerical(n, h, k, I, J, T)  # h ~ dx, k ~ dy
    block = getBlock(h, k)

    A = spzeros(Float64, n, n)
    b = zeros(Float64, n)

    # I é um vetor com o índice da linha  correspondente à particula
    # J é um vetor com o índice da coluna correspondente à particula
    # T é um vetor com a temperatura correspondente à particula (null se não conhecida)

    map = Dict()
    for index = 1:n
        i = I[index]
        j = J[index]
        map[(i, j)] = index
    end

    connect = zeros(UInt32, n, 4)
    for index = 1:n
        i = I[index]
        j = J[index]

        if haskey(map, (i, j - 1))  # Left
            connect[index, 1] = map[(i, j - 1)]
        end
        if haskey(map, (i, j + 1))  # Right
            connect[index, 2] = map[(i, j + 1)]
        end
        if haskey(map, (i - 1, j))  # Bottom
            connect[index, 3] = map[(i - 1, j)]
        end
        if haskey(map, (i + 1, j))  # Top
            connect[index, 4] = map[(i + 1, j)]
        end
    end

    for index = 1:n
        A[index, index] = block[1]
        for column = 1:4
            node = connect[index, column]
            if node != 0
                if isnothing(T[node])
                    A[index, node] = block[column + 1]
                else
                    b[index] += T[node]
                end                    
            end
        end
    end

    for index = 1:n
        if !isnothing(T[index])
            A[index,:] = zeros(Float64, 1, n)
            A[index, index] = 1.0
            b[index] = T[index]
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
