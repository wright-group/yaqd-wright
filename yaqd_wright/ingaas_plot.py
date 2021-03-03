import numpy as np
import matplotlib.pyplot as plt
import yaqc

ingaas = yaqc.Client(38989)
fig, ax = plt.subplots()
fig.subplots_adjust(bottom=0.2)
t = np.arange(-2.0, 2.0, 0.001)
(l,) = ax.plot(t, np.zeros_like(t), lw=2)


def submit():
    try:
        ingaas.measure()
        l.set_xdata(ingaas.get_mappings()["wavelengths"])
        l.set_ydata(ingaas.get_measured()["ingaas"])
    except ConnectionError:
        pass
    ax.relim()
    ax.autoscale_view()
    plt.draw()


timer = fig.canvas.new_timer(interval=200)


@timer.add_callback
def update():
    submit()


timer.start()
plt.show()
