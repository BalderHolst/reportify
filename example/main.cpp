#include <fstream>
#include <iostream>
#include <iomanip>
#include <vector>
#include <cmath>

#include "reportify.h"

// AI DISCLAIMER: This file was written with the help of GitHub Copilot

using std::ifstream;
using std::cout;
using std::endl;
using std::setw;
using std::vector;

double false_position(double (*f)(double), double x, double y, int n, vector<double> * xs = nullptr) {
    for (int i = 0; i < n; i++) {
        double fx = f(x);
        double fy = f(y);

        double x_new = x - ( (x - y) / (fx - fy) ) * fx;
        double y_new = y;

        double fx_new = f(x_new);

        if (fx_new * fy >= 0) y_new = x;

        x = x_new;
        y = y_new;

        if (xs != nullptr) xs->push_back(x);
    }

    return x;
}

int main() {

    TITLE("Assignment 2 - Numerical Methods");
    AUTHOR("Balder W. Holst");

    //! This is exercise 2 from the 2023 exam. This assignment is about the estimating the error on the Regula Falsi (False Position) method.

    SECTION("i) Evaluate the function");

    //! With $x_0 = -2$ and $y_0 = 2$, state (with at least $6$ digits) the values $f(x_0)$ and $f(y_0)$. (HINT: you should get $f(x_0) \simeq 4.46$ and $f(y_0) \simeq -9.38$). Submit the used code.

    SHOW;

    // Define function
    auto f = [] (double x) { return -pow(x, 3) + 2 * cos(x) - exp(-sin(x + 0.5)); };

    // Evaluate function
    cout << "f(x0) = f(-2) = " << f(-2) << endl;
    cout << "f(y0) = f(2)  = " << f(2) << endl;

    OUTPUT;

    SECTION("ii) Find the root");
    //! Perform $15$ iterations with the Regula Falsi (false position) method starting with $x_0 = -2$ and $y_0 = 2$. State (with at least 6 digits) the values $x_{13}$, $x_{14}$ and $x_{15}$. Submit the used code.

    SPAN("False Position Algorithm", __FILE__, 16, 35);

    SHOW;

    int n = 15;

    vector<double> xs;
    false_position(f, -2, 2, n, &xs);

    for (int i = 0; i < xs.size(); i++) {
        cout << "x" << i+1 << " = " << xs[i] << endl;
    }
    cout << endl;

    OUTPUT;

    SECTION("iii) Accuracy estimation");
    //! Assuming that the order is $1$, provide a precise estimate of the accuracy of $x_{15}$. State the estimate together with a clear explanation on how the estimate was arrived at. \\
    //!
    //! We try to approximate the \emph{convergence constant} $C$ as
    //! $$
    //! \frac{d_k}{d_{k-1}} \to C, \quad \mathrm{where} \quad d_k = x_k - x_{k-1}
    //! $$
    //!
    //! The error $\epsilon$ is then given by (for first order convergence)
    //! $$
    //! \epsilon_k = \frac{-C}{1-C}d_k
    //! $$


    vector<double> ds;
    {
        double prev = 0.0;
        for (int i = 0; i < xs.size(); i++) {
            ds.push_back(xs[i] - prev);
            prev = xs[i];
        }
    }

    vector<double> Cs;
    {
        double prev = 0.0;
        for (int i = 0; i < ds.size(); i++) {
            Cs.push_back(ds[i] / prev);
            prev = ds[i];
        }
    }

    vector<double> epsilons;
    {
        for (int i = 0; i < Cs.size(); i++) {
            epsilons.push_back(-Cs[i] / (1 - Cs[i]) * ds[i]);
        }
    }

    CAPTURE;

    int w = 14;
    cout << setw(w) << "k";
    cout << setw(w) << "x";
    cout << setw(w) << "d";
    cout << setw(w) << "C";
    cout << setw(w) << "epsilon";
    cout << endl << std::showpoint;
    for (int i = 0; i < Cs.size(); i++) {
        cout << setw(w) << i + 1;
        cout << setw(w) << xs[i];
        cout << setw(w) << ds[i];
        cout << setw(w) << Cs[i];
        cout << setw(w) << epsilons[i];
        cout << endl;
    }

    OUTPUT;

    //! After 15 iterations, $x \simeq x_{15} = 0.932286$. The error is estimated to be $\epsilon \simeq \epsilon_{15} = 0.00247971$ assuming a convergence order of $1$.

    return 0;
}
